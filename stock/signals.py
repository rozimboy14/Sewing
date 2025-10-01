from django.db.models import Sum
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save

from production.models import MonthPlaningOrder, LineOrders, NormCategory
from stock.models import StockEntryVariant, Stock, StockVariant


def recalc_stock_quantity(order):
    from production.models import MonthPlaningOrder

    try:
        mpo = MonthPlaningOrder.objects.get(order=order)
        stock_total = StockVariant.objects.filter(
            stock__warehouse=mpo.month_planing.warehouse,
            stock__order=order
        ).aggregate(
            total=Sum("quantity")
        )["total"] or 0

        mpo.stock_quantity = stock_total
        mpo.save(update_fields=["stock_quantity"])
        return mpo.stock_quantity
    except MonthPlaningOrder.DoesNotExist:
        return None



@receiver([post_save, post_delete], sender=Stock)
def update_fact_quantity(sender, instance, **kwargs):
    recalc_stock_quantity(instance.order)

def recalc_all_month_planing_orders():
    from production.models import MonthPlaningOrder
    updated = 0
    for mpo in MonthPlaningOrder.objects.all():
        # stock qayta hisoblash
        stock_total = StockVariant.objects.filter(
            stock__order=mpo.order,
        stock__warehouse = mpo.month_planing.warehouse
        ).aggregate(
            total=Sum("quantity")
        )["total"] or 0
        mpo.stock_quantity = stock_total

        # fakt qayta hisoblash
        agg = NormCategory.objects.filter(
            order=mpo.order,
            production_norm__production_report__warehouse=mpo.month_planing.warehouse,
            production_norm__production_report__year=mpo.month_planing.year,
            production_norm__production_report__month=mpo.month_planing.month,
        ).aggregate(
            total_sort_1=Sum('total_sort_1'),
            total_sort_2=Sum('total_sort_2')
        )

        total_fact = (agg['total_sort_1'] or 0) + (agg['total_sort_2'] or 0)
        mpo.fact_quantity = total_fact

        mpo.save(update_fields=["stock_quantity", "fact_quantity"])
        updated += 1
    return updated

@receiver([post_save, post_delete], sender=NormCategory)
def update_fact_quantity_norm(sender, instance, **kwargs):
    try:
        mpo = MonthPlaningOrder.objects.get(order=instance.order,
                                            month_planing__warehouse=instance.production_norm.production_report.warehouse,
                                            month_planing__year=instance.production_norm.production_report.year,
                                            month_planing__month=instance.production_norm.production_report.month)
        mpo.recalc_fact_quantity()
    except MonthPlaningOrder.DoesNotExist:
        pass
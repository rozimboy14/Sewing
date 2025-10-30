# production/signals.py
import datetime
from django.db.models import Sum
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError as DjangoValidationError
from production import models
from production.models import LineOrders, MonthPlaning, MonthPlaningOrder, \
    Daily, ProductionReport, Line, NormCategory, LineDailyOutput
from services.stock_service import decrease_stock_variant_bulk, \
    increase_stock_variant_bulk, StockPackagingService


def update_norm_category_fact(norm_category: NormCategory):
    agg = LineOrders.objects.filter(order=norm_category).aggregate(
        total_sort_1=Sum('sort_1'),
        total_sort_2=Sum('sort_2'),
        total_defect=Sum('defect_quantity')
    )
    norm_category.total_sort_1 = agg['total_sort_1'] or 0
    norm_category.total_sort_2 = agg['total_sort_2'] or 0
    norm_category.total_defect = agg['total_defect'] or 0
    norm_category.save(
        update_fields=['total_sort_1', 'total_sort_2', 'total_defect'])
    update_line_daily_output(norm_category)


def update_line_daily_output(norm_category: NormCategory):
    today = datetime.date.today()
    line = norm_category.production_norm.line
    output, created = LineDailyOutput.objects.get_or_create(
        line=line,
        norm_category=norm_category,
        date=today,
        defaults={'sort_1': 0, 'sort_2': 0, 'defect_quantity': 0}
    )
    agg = LineOrders.objects.filter(order=norm_category).aggregate(
        total_sort_1=Sum('sort_1'),
        total_sort_2=Sum('sort_2'),
        total_defect=Sum('defect_quantity')
    )

    output.sort_1 = agg['total_sort_1'] or 0
    output.sort_2 = agg['total_sort_2'] or 0
    output.defect_quantity = agg['total_defect'] or 0
    output.save(update_fields=['sort_1', 'sort_2', "defect_quantity"])


@receiver(post_save, sender=LineOrders)
def lineorders_post_save(sender, instance: LineOrders, **kwargs):
    update_norm_category_fact(instance.order)


@receiver(post_delete, sender=LineOrders)
def lineorders_post_delete(sender, instance: LineOrders, **kwargs):
    update_norm_category_fact(instance.order)


@receiver(post_save, sender=MonthPlaningOrder)
def update_planing_quantity_on_save(sender, instance, **kwargs):
    month_planing = instance.month_planing
    total_planed = month_planing.month_planing_order.aggregate(
        total=models.Sum('planed_quantity'))['total'] or 0

    month_planing.planing_quantity = total_planed
    month_planing.save(update_fields=['planing_quantity'])


@receiver(post_delete, sender=MonthPlaningOrder)
def delete_planing_quantity_on_save(sender, instance, **kwargs):
    month_planing = instance.month_planing
    total_planed = month_planing.month_planing_order.aggregate(
        total=models.Sum('planed_quantity'))['total'] or 0
    month_planing.planing_quantity = total_planed
    month_planing.save(update_fields=['planing_quantity'])


@receiver([post_save, post_delete], sender=Line)
def update_monthplaning_fact(sender, instance, **kwargs):
    try:
        mpo = MonthPlaning.objects.get(

            warehouse=instance.line_daily.production_report.warehouse,
            year=instance.line_daily.production_report.year,
            month=instance.line_daily.production_report.month,
        )
        mpo.recalc_fact_quantity()
    except MonthPlaning.DoesNotExist:
        pass


@receiver([post_save, post_delete], sender=NormCategory)
def update_monthplaningorder_fact(sender, instance, **kwargs):
    try:
        mpo = MonthPlaningOrder.objects.get(
            order=instance.order,
            month_planing__warehouse=instance.production_norm.production_report.warehouse,
            month_planing__year=instance.production_norm.production_report.year,
            month_planing__month=instance.production_norm.production_report.month,
        )
        mpo.recalc_fact_quantity()
    except MonthPlaningOrder.DoesNotExist:
        pass


@receiver(pre_save, sender=LineOrders)
def update_stock_on_lineorders_save(sender, instance, **kwargs):
    if instance.pk:
        old_instance = LineOrders.objects.get(pk=instance.pk)
        old_total = (old_instance.sort_1 or 0) + (old_instance.sort_2 or 0) + (
            old_instance.defect_quantity or 0
        )
    else:
        old_total = 0

    new_total = (instance.sort_1 or 0) + (instance.sort_2 or 0) + (
        instance.defect_quantity or 0
    )
    diff = new_total - old_total

    if diff == 0:
        return

    warehouse = instance.order_line.line_daily.production_report.warehouse
    order_variant = instance.order.order_variant

    if diff > 0:
        # mahsulot qo‘shish kerak
        decrease_stock_variant_bulk(order_variant, warehouse, diff)

    else:
        increase_stock_variant_bulk(order_variant, warehouse, -diff)


@receiver(post_delete, sender=LineOrders)
def update_stock_on_lineorders_delete(sender, instance, **kwargs):

    warehouse = instance.order_line.line_daily.production_report.warehouse
    order_variant = instance.order.order_variant
    quantity = (instance.sort_1 or 0) + (instance.sort_2 or 0) + (
                instance.defect_quantity or 0)
    increase_stock_variant_bulk(order_variant, warehouse, quantity)



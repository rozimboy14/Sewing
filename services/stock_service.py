from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError

from production.models import ProductionReport, Daily, LineOrders, \
    NormCategory, Line, ProductionNorm
from sewing.models import ArticleAccessory
from stock.models import Stock, StockVariant, AccessoryStock
import datetime
import calendar

def check_stock_variant_bulk(line_order, quantity):
    """Variant va aksessuarlarni faqat tekshiradi, stokni kamaytirmaydi"""
    norm_category = line_order.order
    order_variant = norm_category.order_variant
    warehouse = line_order.order_line.line_daily.production_report.warehouse

    stock = StockVariant.objects.filter(
        stock__order=norm_category.order,
        variant=order_variant,
        stock__warehouse=warehouse
    ).first()
    if not stock or stock.quantity < quantity:
        raise ValidationError(
            {
                "detail": f"{warehouse.name} omborda yetarli mahsulot yo‘q: "
                          f"{norm_category.order.full_name}-{order_variant.name}. "
                          f"Qoldiq: {stock.quantity if stock else 0}, kerak: {quantity}"
            }
        )

    # Aksessuarlarni tekshirish
    accessories = ArticleAccessory.objects.filter(article=order_variant.order.article)
    for aa in accessories:
        acc_stock = AccessoryStock.objects.filter(accessory=aa.accessory, warehouse=warehouse).first()
        if not acc_stock or acc_stock.total_quantity < quantity * aa.quantity:
            raise ValidationError(
                {
                    "detail": f"{warehouse.name} omborda aksessuar yetarli emas: {aa.accessory.name}. "
                              f"Qoldiq: {acc_stock.total_quantity if acc_stock else 0}, kerak: {quantity * aa.quantity}"
                }
            )


@transaction.atomic
def decrease_stock_variant_bulk(order_variant, warehouse, quantity):
    """OrderVariant + aksessuarni kamaytiradi atomically"""
    if quantity <= 0:
        return

    stock, _ = Stock.objects.get_or_create(order=order_variant.order, warehouse=warehouse)
    sv, _ = StockVariant.objects.get_or_create(stock=stock, variant=order_variant)

    # Atomic update F()
    StockVariant.objects.filter(pk=sv.pk).update(quantity=F('quantity') - quantity)

    accessories = ArticleAccessory.objects.filter(article=order_variant.order.article)
    acc_stocks = {a.accessory_id: a for a in AccessoryStock.objects.filter(
        accessory__in=[aa.accessory for aa in accessories], warehouse=warehouse
    )}

    for aa in accessories:
        acc_stock = acc_stocks.get(aa.accessory_id)
        if not acc_stock:
            acc_stock = AccessoryStock.objects.create(accessory=aa.accessory, warehouse=warehouse, total_quantity=0)
            acc_stocks[aa.accessory_id] = acc_stock

        AccessoryStock.objects.filter(pk=acc_stock.pk).update(
            total_quantity=F('total_quantity') - quantity * aa.quantity
        )


@transaction.atomic
def increase_stock_variant_bulk(order_variant, warehouse, quantity):
    """OrderVariant + aksessuarni ko‘paytiradi atomically"""
    if quantity <= 0:
        return

    stock, _ = Stock.objects.get_or_create(order=order_variant.order, warehouse=warehouse)
    sv, _ = StockVariant.objects.get_or_create(stock=stock, variant=order_variant)
    StockVariant.objects.filter(pk=sv.pk).update(quantity=F('quantity') + quantity)

    accessories = ArticleAccessory.objects.filter(article=order_variant.order.article)
    acc_stocks = {a.accessory_id: a for a in AccessoryStock.objects.filter(
        accessory__in=[aa.accessory for aa in accessories], warehouse=warehouse
    )}

    for aa in accessories:
        acc_stock = acc_stocks.get(aa.accessory_id)
        if not acc_stock:
            acc_stock = AccessoryStock.objects.create(accessory=aa.accessory, warehouse=warehouse, total_quantity=0)
            acc_stocks[aa.accessory_id] = acc_stock

        AccessoryStock.objects.filter(pk=acc_stock.pk).update(
            total_quantity=F('total_quantity') + quantity * aa.quantity
        )


from django.db import transaction
from packaging.models import StockPackaging, StockPackagingVariant


class StockPackagingService:
    @staticmethod
    @transaction.atomic
    def increase(order, warehouse, order_variant, sort_1=0, sort_2=0):
        """Packaging qty ko‘paytirish"""
        sp, _ = StockPackaging.objects.get_or_create(order=order, warehouse=warehouse)
        sp_variant, _ = StockPackagingVariant.objects.get_or_create(stock_packaging=sp, variant=order_variant)

        sp_variant.sort_1 = max(sp_variant.sort_1 + sort_1, 0)
        sp_variant.sort_2 = max(sp_variant.sort_2 + sort_2, 0)

        sp_variant.save()
        return sp_variant

    @staticmethod
    @transaction.atomic
    def decrease(order, warehouse, order_variant, sort_1=0, sort_2=0):
        """Packaging qty kamaytirish, lekin record bo‘lmasa ham yaratadi"""
        sp, _ = StockPackaging.objects.get_or_create(order=order,
                                                     warehouse=warehouse)
        sp_variant, _ = StockPackagingVariant.objects.get_or_create(
            stock_packaging=sp, variant=order_variant)

        sp_variant.sort_1 = max(sp_variant.sort_1 - sort_1, 0)
        sp_variant.sort_2 = max(sp_variant.sort_2 - sort_2, 0)
        sp_variant.save()
        return sp_variant

def create_production_report_with_daily(warehouse, year: int, month: str, **kwargs):
    """
    ProductionReport yaratadi va unga tegishli barcha kunlik (Daily) yozuvlarini yaratadi.
    """
    # Avval ProductionReport yaratamiz
    report = ProductionReport.objects.create(
        warehouse=warehouse,
        year=year,
        month=month,
        **kwargs
    )

    # Oydagi kunlar sonini aniqlash
    _, days_in_month = calendar.monthrange(year, int(month))

    # Daily yozuvlarini tayyorlab qo'yamiz
    daily_objects = []
    for day in range(1, days_in_month + 1):
        date = datetime.date(year, int(month), day)
        daily_objects.append(Daily(production_report=report, date=date))

    Daily.objects.bulk_create(daily_objects)

    return report

class NormCategoryService:
    @staticmethod
    @transaction.atomic
    def create_norm_category(production_report, line, ):
        """
        NormCategory yaratadi va har bir Daily → Line → LineOrders ni update qiladi
        """
        # 1️⃣ NormCategory yaratish
        production_norm  = ProductionNorm.objects.create(
            production_report=production_report,
            line=line,

        )

        # 2️⃣ Oyning barcha Daily yozuvlarini olish

        for daily in production_report.daily_report.all():
            line, _ = Line.objects.get_or_create(
                line_daily=daily,
                production_norm=production_norm
            )




        return production_norm

    @staticmethod
    @transaction.atomic
    def update_norm_category(norm_category, **kwargs):
        """
        NormCategory update qiladi va Daily → Line → LineOrders ni update qiladi
        """
        # update fields
        for key, value in kwargs.items():
            setattr(norm_category, key, value)
        norm_category.save()

        # Line va Daily yangilash
        try:
            line_order = norm_category.order_line_orders.first()
            if line_order:
                line_order.save()
                line_order.order_line.recalc_total_quantity()
                line_order.order_line.line_daily.recalc_total_quantity()
        except LineOrders.DoesNotExist:
            pass

        # ProductionNorm va ProductionReport ni recalc qilish
        norm_category.production_norm.recalc_total_quantity()
        return norm_category

    @staticmethod
    @transaction.atomic
    def delete_norm_category(norm_category):
        """
        NormCategory o‘chiradi va Daily → Line → LineOrders ni update qiladi
        """
        try:
            line_order = norm_category.order_line_orders.first()
            if line_order:
                line = line_order.order_line
                daily = line.line_daily
                line_order.delete()
                line.recalc_total_quantity()
                daily.recalc_total_quantity()
        except LineOrders.DoesNotExist:
            pass

        # NormCategory o‘chirish
        norm_category.delete()
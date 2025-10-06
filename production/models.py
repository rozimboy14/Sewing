from django.db import models, transaction
from django.db.models import PositiveIntegerField, Sum, Value, F
import datetime

from django.db.models.functions import Coalesce

from sewing.models import Order, SewingCategory, OrderVariant
from stock.models import Stock, Warehouse, StockVariant

# Create your models here.


current_year = datetime.date.today().year
YEAR_CHOICES = [(y, y) for y in range(current_year, current_year + 6)]

MONTH_CHOICES = [
    ('01', 'Yanvar'),
    ('02', 'Fevral'),
    ('03', 'Mart'),
    ('04', 'Aprel'),
    ('05', 'May'),
    ('06', 'Iyun'),
    ('07', 'Iyul'),
    ('08', 'Avgust'),
    ('09', 'Sentabr'),
    ('10', 'Oktyabr'),
    ('11', 'Noyabr'),
    ('12', 'Dekabr'),
]


class ProductionLine(models.Model):
    warehouse  =models.ForeignKey(Warehouse,
                                       on_delete=models.CASCADE,related_name='production_lines')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    @property
    def full_name(self):
        return f"{self.name}-Линия"


class ProductionReport(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    year = models.IntegerField(choices=YEAR_CHOICES)
    month = models.CharField(max_length=2, choices=MONTH_CHOICES)
    total_sort_1 = models.PositiveIntegerField(default=0)
    total_sort_2 = models.PositiveIntegerField(default=0)
    total_defect = models.PositiveIntegerField(default=0)
    total_norm = models.PositiveIntegerField(default=0)
    day = models.CharField(max_length=100, blank=True, null=True)
    comment = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.year}-{self.month}"

    def recalc_totals(self):
        agg = self.production_norm.aggregate(
            total_sort_1=Coalesce(Sum('total_sort_1'), 0),
            total_sort_2=Coalesce(Sum('total_sort_2'), 0),
            total_defect=Coalesce(Sum('total_defect'), 0),
        )
        self.total_sort_1 = agg['total_sort_1']
        self.total_sort_2 = agg['total_sort_2']
        self.total_defect = agg['total_defect']
        self.save(
            update_fields=["total_sort_1", "total_sort_2", "total_defect"])


    def update_category_summaries(self):
        ProductionCategorySummary.objects.filter(
            production_report=self
        ).delete()

        # Normani hisoblash
        norm_data = (
            NormCategory.objects.filter(
                production_norm__production_report=self
            )
            .values('order__article__sewing_category')
            .annotate(total_norm=Sum('norm'))
        )

        # Faktni hisoblash

        actual_data = (
            NormCategory.objects.filter(
                production_norm__production_report=self
            )
            .values(
                'order__article__sewing_category')
            .annotate(
                total_quantity=Coalesce(
                    Sum(F('total_sort_1') + Coalesce(F('total_sort_2'),
                                                     Value(0))), 0)
            )
        )

        actual_map = {
            item['order__article__sewing_category']: item['total_quantity']
            for item in actual_data
        }

        for norm_item in norm_data:
            category_id = norm_item[
                'order__article__sewing_category']  # ✅ to‘g‘ri kalit
            norm = norm_item['total_norm']
            actual = actual_map.get(category_id, 0)

            ProductionCategorySummary.objects.create(
                production_report=self,
                category_id=category_id,
                norm=norm,
                actual=actual
            )


class ProductionCategorySummary(models.Model):
    production_report = models.ForeignKey(
        ProductionReport, on_delete=models.CASCADE,
        related_name="category_summaries"
    )
    category = models.ForeignKey(SewingCategory, on_delete=models.CASCADE)
    norm = models.PositiveIntegerField(default=0)
    actual = models.PositiveIntegerField(default=0)


class ProductionNorm(models.Model):
    production_report = models.ForeignKey(ProductionReport,
                                          on_delete=models.CASCADE,
                                          related_name="production_norm")
    line = models.ForeignKey(ProductionLine, on_delete=models.CASCADE)
    total_sort_1 = models.PositiveIntegerField(blank=True, null=True)
    total_sort_2 = models.PositiveIntegerField(blank=True, null=True)
    total_defect = models.PositiveIntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.production_report.recalc_totals()

    def delete(self, *args, **kwargs):
        report = self.production_report
        super().delete(*args, **kwargs)
        report.recalc_totals()

    def __str__(self):
        return (f"{self.line.full_name}-{self.line.warehouse}"
                f" - {self.production_report.month}  ")

    def recalc_total_quantity(self):
        sort_1 = self.norm_category.aggregate(total=Coalesce(Sum("total_sort_1"), 0))[
            'total']
        sort_2 = self.norm_category.aggregate(total=Coalesce(Sum("total_sort_2"), 0))[
            'total']
        defect_quantity = \
        self.norm_category.aggregate(total=Coalesce(Sum("total_defect"), 0))[
            'total']
        self.total_sort_1 = sort_1
        self.total_sort_2 = sort_2
        self.total_defect = defect_quantity
        self.save(
            update_fields=["total_sort_1", "total_sort_2", "total_defect"])


class NormCategory(models.Model):
    production_norm = models.ForeignKey(ProductionNorm,
                                        on_delete=models.CASCADE,
                                        related_name="norm_category")
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    order_variant =models.ForeignKey(OrderVariant, on_delete=models.CASCADE,
                                     blank=True, null=True)
    total_sort_1 = models.PositiveIntegerField(blank=True, null=True)
    total_sort_2 = models.PositiveIntegerField(blank=True, null=True)
    total_defect = models.PositiveIntegerField(blank=True, null=True)
    norm = models.PositiveIntegerField()
    @property
    def full_name(self):
        return f"{self.order.full_name}-{self.order_variant}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        report = self.production_norm.production_report
        total_norm = NormCategory.objects.filter(
            production_norm__production_report=report
        ).aggregate(total_norm=Sum('norm'))['total_norm'] or 0

        report.total_norm = total_norm
        report.save(update_fields=["total_norm"])

        self.production_norm.recalc_total_quantity()


    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.production_norm.recalc_total_quantity()
    def __str__(self):
        return (f"{self.production_norm.line.full_name}-{self.order}"
                f"-{self.order_variant}-"
                f"{self.production_norm.production_report}")

class Daily(models.Model):
    production_report = models.ForeignKey(ProductionReport,
                                          on_delete=models.CASCADE,
                                          related_name='daily_report')
    date = models.DateField()
    sort_1 = models.PositiveIntegerField(blank=True, null=True)
    sort_2 = models.PositiveIntegerField(blank=True, null=True)
    defect_quantity = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.date.strftime("%d %B %A")

    def recalc_total_quantity(self):
        sort_1 = self.lines.aggregate(total=Coalesce(Sum("sort_1"), 0))['total']
        sort_2 = self.lines.aggregate(total=Coalesce(Sum("sort_2"), 0))['total']
        defect_quantity = self.lines.aggregate(total=Coalesce(Sum("defect_quantity"), 0))['total']
        self.sort_1 = sort_1
        self.sort_2 = sort_2
        self.defect_quantity = defect_quantity
        self.save(update_fields=["sort_1", "sort_2", "defect_quantity"])



class Line(models.Model):
    line_daily = models.ForeignKey(Daily, on_delete=models.CASCADE,related_name='lines')
    production_norm = models.ForeignKey(
        ProductionNorm,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    sort_1 = models.PositiveIntegerField(blank=True, null=True)
    sort_2 = models.PositiveIntegerField(blank=True, null=True)
    defect_quantity = models.PositiveIntegerField(blank=True, null=True)

    @property
    def line(self):
        # ProductionLineni olish
        return self.production_norm.line.full_name

    def __str__(self):
        return f"{self.line_daily} {self.production_norm.line.full_name}"

    @property
    def total_quantity(self):
        return (self.sort_1 or 0) + (self.sort_2 or 0)

    def recalc_total_quantity(self):
        agg = self.order_line.aggregate(
            total_sort_1=Coalesce(Sum("sort_1"), 0),
            total_sort_2=Coalesce(Sum("sort_2"), 0),
            total_defect=Coalesce(Sum("defect_quantity"), 0)
        )
        self.sort_1 = agg['total_sort_1']
        self.sort_2 = agg['total_sort_2']
        self.defect_quantity = agg['total_defect']
        self.save(update_fields=["sort_1", "sort_2", "defect_quantity"])

        # Daily-ni ham yangilaymiz

        self.line_daily.recalc_total_quantity()

class LineOrders(models.Model):
    order_line = models.ForeignKey(Line, on_delete=models.CASCADE,
                                   related_name='order_line')
    order = models.ForeignKey(NormCategory, on_delete=models.CASCADE,
                              related_name='order_line_orders')
    sort_1 = models.IntegerField()
    sort_2 =models.IntegerField(blank=True, null=True)
    defect_quantity = models.PositiveIntegerField(default=0)


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.order_line.recalc_total_quantity()  # ✅ Line qayta hisoblanadi

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.order_line.recalc_total_quantity()
class LineDailyOutput(models.Model):
    line = models.ForeignKey(ProductionLine, on_delete=models.CASCADE, related_name='daily_outputs')
    norm_category = models.ForeignKey(NormCategory, on_delete=models.CASCADE, related_name='daily_outputs')
    date = models.DateField()
    sort_1 = models.IntegerField(blank=True, null=True)
    sort_2 = models.IntegerField(blank=True, null=True)
    defect_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('line', 'norm_category', 'date')

class MonthPlaning(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE,)
    year = models.IntegerField(choices=YEAR_CHOICES)
    month = models.CharField(max_length=2, choices=MONTH_CHOICES)
    comment = models.CharField( max_length=100,blank=True,null=True)
    day_planing = models.CharField( max_length=100)
    planing_quantity = models.IntegerField(blank=True, null=True)
    fact_quantity = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.year} {self.month}"

    def recalc_fact_quantity(self):
        total = Line.objects.filter(
            line_daily__production_report__warehouse=self.warehouse,
            line_daily__production_report__year=self.year,
            line_daily__production_report__month=self.month,
        ).aggregate(
            total=Coalesce(Sum(F('sort_1') + Coalesce(F('sort_2'), 0)), 0)
        )['total']
        self.fact_quantity = total
        self.save(update_fields=["fact_quantity"])
        return self.fact_quantity


class MonthPlaningOrder(models.Model):
    month_planing = models.ForeignKey(MonthPlaning,
                                      on_delete=models.CASCADE,related_name='month_planing_order')
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    planed_quantity = models.IntegerField()
    stock_quantity = models.IntegerField(blank=True, null=True)
    fact_quantity = models.IntegerField(blank=True, null=True)
    comment = models.CharField( max_length=100,blank=True,null=True)
    def __str__(self):
        return f"{self.month_planing} {self.order.full_name}"

    def recalc_fact_quantity(self):
        agg = NormCategory.objects.filter(
            order=self.order,
            production_norm__production_report__warehouse=self.month_planing.warehouse,
            production_norm__production_report__year=self.month_planing.year,
            production_norm__production_report__month=self.month_planing.month,
        ).aggregate(
            total_sort_1=Sum('total_sort_1'),
            total_sort_2=Sum('total_sort_2')
        )

        total = (agg['total_sort_1'] or 0) + (agg['total_sort_2'] or 0)
        self.fact_quantity = total
        self.save(update_fields=["fact_quantity"])
        return self.fact_quantity

    def recalc_stock_quantity(self):
        total = StockVariant.objects.filter(
            stock__order=self.order,
            stock__warehouse=self.month_planing.warehouse
        ).aggregate(total=Sum('quantity'))['total'] or 0

        self.stock_quantity = total
        self.save(update_fields=["stock_quantity"])
        return self.stock_quantity

from django.db import models
from django.db.models import Sum

from sewing.models import Order, OrderVariant
from stock.models import Warehouse


# Create your models here.
class StockPackaging(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              related_name="stocks_packaging")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE,
                                  related_name="stocks_packaging_warehouse")

    def __str__(self):
        return f"Stock: {self.order}"

    @property
    def total_sort_1(self):
        return self.stock_packaging_variants.aggregate(total=Sum("sort_1"))[
            "total"] or 0
    @property
    def total_sort_2(self):
        return self.stock_packaging_variants.aggregate(total=Sum("sort_2"))[
            "total"] or 0



class StockPackagingVariant(models.Model):
    stock_packaging = models.ForeignKey(
        "StockPackaging", on_delete=models.CASCADE,
        related_name="stock_packaging_variants"
    )
    variant = models.ForeignKey("sewing.OrderVariant",
                                on_delete=models.CASCADE)
    sort_1 = models.IntegerField(default=0)
    sort_2 = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["stock_packaging", "variant"],
                name="uniq_stock_packaging_variant"
            ),

            models.CheckConstraint(
                check=(
                        models.Q(sort_1__gte=0) &
                        models.Q(sort_2__gte=0)
                ),
                name="packaging_qty_gte_0",
            ),

        ]

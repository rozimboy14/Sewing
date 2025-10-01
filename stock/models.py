from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone
from sewing.models import Order, OrderVariant, Accessory


# === STOCK MODELS ===

class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)

    def __str__(self):
        return self.name



class Stock(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              related_name="stocks")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE,
                                  related_name="stocks_warehouse")

    def __str__(self):
        return f"Stock: {self.order}"
    @property
    def total_quantity(self):
        return self.stock_variants.aggregate(total=Sum("quantity"))["total"] or 0

class StockVariant(models.Model):
    stock = models.ForeignKey(
        "Stock", on_delete=models.CASCADE, related_name="stock_variants"
    )
    variant = models.ForeignKey("sewing.OrderVariant",
                                on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["stock", "variant"],
                                    name="uniq_stock_variant"),
            models.CheckConstraint(check=models.Q(quantity__gte=0),
                                   name="qty_gte_0"),
        ]

    def __str__(self):
        return f"{self.variant.name} ({self.quantity} dona)"


# === KIRIM / CHIQIM JADVALI ===

class TotalEntry(models.Model):
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="total_entries"
    )
    created_date = models.DateTimeField(default=timezone.now)
    comment = models.CharField(max_length=120, blank=True, null=True)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"Entry: {self.created_date}"

    def confirm(self):
        if self.confirmed:
            return
        with transaction.atomic():
            # === ORDER / VARIANT ===
            for se in self.stock_entries.all():
                stock = _get_stock_by_order(se.order, self.warehouse)
                for sev in se.variants.all():
                    sv, _ = StockVariant.objects.get_or_create(
                        stock=stock,
                        variant=sev.variant,
                        defaults={"quantity": 0}
                    )
                    sv.quantity = models.F("quantity") + sev.quantity
                    sv.save(update_fields=["quantity"])

                    # 🟢 umumiy stock miqdorini ham oshirish


            # === ACCESSORY ===
            for ase in self.accessory_stock_entries.all():
                stock, _ = AccessoryStock.objects.get_or_create(
                    accessory=ase.accessory,
                    warehouse=self.warehouse
                )
                stock.total_quantity = models.F(
                    "total_quantity") + ase.quantity
                stock.save(update_fields=["total_quantity"])

            self.confirmed = True
            self.save(update_fields=["confirmed"])
class StockEntry(models.Model):
    total_entry = models.ForeignKey(TotalEntry, on_delete=models.CASCADE,
                                    related_name="stock_entries")
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.order}"


def _get_stock_by_order(order, warehouse):
    stock, _ = Stock.objects.get_or_create(order=order,
                                           warehouse=warehouse,
                                        )
    return stock


class StockEntryVariant(models.Model):
    stock_entry = models.ForeignKey(StockEntry, on_delete=models.CASCADE,
                                    related_name="variants")
    variant = models.ForeignKey(OrderVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ("stock_entry", "variant")

    def __str__(self):
        return f"{self.stock_entry} | {self.variant.name} | {self.quantity} ta"


# === AKSESSUAR STOCK  ===

class AccessoryStock(models.Model):
    accessory = models.ForeignKey(Accessory, on_delete=models.CASCADE)
    total_quantity = models.PositiveIntegerField(default=0)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE,
                                  related_name="accessory_warehouse")

    def __str__(self):
        return f"{self.accessory} ({self.total_quantity} dona)"


class AccessoryStockEntry(models.Model):
    total_entry = models.ForeignKey(
        TotalEntry, on_delete=models.CASCADE,
        related_name='accessory_stock_entries'
    )
    accessory = models.ForeignKey(Accessory, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    date = models.DateField(auto_now_add=True)


    def __str__(self):
        return f"Aksessuar kirim: {self.accessory} - {self.quantity} ta"

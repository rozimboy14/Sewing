from django.contrib import admin
from .models import (

    Warehouse, TotalEntry, Stock, StockVariant)

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name','location')
    search_fields = ('name',)


@admin.register(TotalEntry)
class TotalEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment', 'warehouse','created_date')
    search_fields = ('comment',)


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'warehouse','total_quantity')


@admin.register(StockVariant)
class StockVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'stock','variant','quantity')



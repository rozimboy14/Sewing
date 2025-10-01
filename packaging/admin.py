from django.contrib import admin

from packaging.models import StockPackaging, StockPackagingVariant


# Register your models here.
@admin.register(StockPackaging)
class StockPackagingAdmin(admin.ModelAdmin):
    list_display = ['id', 'warehouse','order','total_sort_1','total_sort_2']




@admin.register(StockPackagingVariant)
class StockPackagingVariantAdmin(admin.ModelAdmin):
    list_display = ['id', 'stock_packaging','variant','sort_1','sort_2']


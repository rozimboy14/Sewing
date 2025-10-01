from django.contrib import admin


from .models import (
    ProductionLine,
    ProductionReport,
    Daily,
    Line,
    LineOrders, ProductionNorm, NormCategory, LineDailyOutput
)



@admin.register(ProductionLine)
class ProductionReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'warehouse','name',]




@admin.register(ProductionReport)
class ProductionReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'month']
    list_filter = ['month']


@admin.register(Daily)
class DailyAdmin(admin.ModelAdmin):
    list_display = ['id', 'production_report', 'date']
    list_filter = ['date', 'production_report']


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = ['id', 'line_daily', 'production_norm']
    list_filter = ['line_daily', 'production_norm']



@admin.register(LineOrders)
class LineOrdersAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_line','order','sort_1','sort_2','defect_quantity']



@admin.register(ProductionNorm)
class ProductionNormAdmin(admin.ModelAdmin):
    list_display = ['id', 'production_report', 'line']

@admin.register(NormCategory)
class NormCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'production_norm', 'order','order_variant','norm','total_sort_1',
                    'total_sort_2','total_defect']

@admin.register(LineDailyOutput)
class LineDailyOutputAdmin(admin.ModelAdmin):
    list_display = ['id', 'line', 'norm_category','date','created_at','sort_1',
                    'sort_2','defect_quantity']
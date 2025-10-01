from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    ProductionLineViewSet, ProductionReportViewSet,
    LineViewSet, LineOrdersViewSet, DailyViewSet, NormCategoryViewSet,
    ProductionNormViewSet, ProductionCategorySummaryViewSet,
    MonthPlaningViewSet, MonthPlaningOrderViewSet, refresh_stock_quantity,
    refresh_all_month_planing_orders, upload_excel, NormCategoryByReportView
)

router = DefaultRouter()
router.register(r'production-lines', ProductionLineViewSet)
router.register(r'production-reports', ProductionReportViewSet)
router.register(r'line', LineViewSet)
router.register(r'line-orders', LineOrdersViewSet,basename='line-orders')
router.register(r'daily', DailyViewSet)
router.register(r'norm-category', NormCategoryViewSet)
router.register(r'production-norm', ProductionNormViewSet)
router.register(r'production-category', ProductionCategorySummaryViewSet)
router.register(r'month-planing', MonthPlaningViewSet)
router.register(r'month-planing-order', MonthPlaningOrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('refresh-stock/',refresh_all_month_planing_orders),
    path('upload/', upload_excel, name='upload_excel'),
path('reports/<int:report_id>/norm-categories/', NormCategoryByReportView.as_view(), name='norm-categories-by-report'),

]

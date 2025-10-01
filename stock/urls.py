from rest_framework.routers import DefaultRouter
from django.urls import path, include


from .views import StockView, StockEntryView, TotalEntryView, \
    StockCategoryViewSet, StockBrandListView, AccessoryStockEntryView, \
    StockAccessoryBrandListView, StockAccessoryTypeListView, \
    AccessoryStockView, AccessoryStockExportPDFView, \
    StockEntryViewSet, StockTotalQuantityListView ,\
    total_entry_pdf, WarehouseViewSet

router = DefaultRouter()
router.register('stock',StockView,basename='stock')
router.register('warehouse',WarehouseViewSet,basename='warehouse')
router.register('accessory-stock',AccessoryStockView,
                basename='accessory-stock')
router.register('stock_entry',StockEntryViewSet,basename='stock_entry')
router.register('accessory_stock_entry',AccessoryStockEntryView,
               )
router.register('total_entry',TotalEntryView,basename='total_entry')

urlpatterns = [
    path('', include(router.urls)),
    path('total_stock/', StockTotalQuantityListView.as_view()),
    path('by-category/', StockCategoryViewSet.as_view()),
    path('by-brand/', StockBrandListView.as_view()),
    path('by-brand_accessory/', StockAccessoryBrandListView.as_view()),

    path('by-accessory_type/', StockAccessoryTypeListView.as_view()),
    path('total_entry_pdf/<int:total_entry_id>/pdf/',
         total_entry_pdf),
   path('accessory-stock/export-pdf/', AccessoryStockExportPDFView.as_view(), name='accessory-stock-export-pdf'),
]

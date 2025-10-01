from rest_framework.routers import DefaultRouter
from django.urls import path, include

from packaging.views import (StockPackagingViewSet,
                             StockPackagingVariantViewSet,
                             StockPackagingBrandListView, StockCategoryViewSet)

router = DefaultRouter()
router.register(r'packaging-stock', StockPackagingViewSet)
router.register(r'packaging-variant-stock', StockPackagingVariantViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('stock-packaging-brand/', StockPackagingBrandListView.as_view()),
    path('stock-packaging-category/', StockCategoryViewSet.as_view()),

]
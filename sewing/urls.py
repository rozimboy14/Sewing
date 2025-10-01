from rest_framework.routers import DefaultRouter
from django.urls import path, include

from sewing.views import (BrandViewSet, SpecificationViewSet, OrderViewSet,
                          PackagingCategoryViewSet, ArticleViewSet,
                          SewingCategoryViewSet, AccesoryViewSet)

router = DefaultRouter()

router.register('brand', BrandViewSet)
router.register('specification', SpecificationViewSet)
router.register('order', OrderViewSet)
router.register('packaging_category', PackagingCategoryViewSet)
router.register('article', ArticleViewSet)
router.register('sewing_category', SewingCategoryViewSet)
router.register('accessory', AccesoryViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
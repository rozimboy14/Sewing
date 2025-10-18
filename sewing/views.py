from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.views import APIView

from services.custom_pagination import CustomPagination
from sewing.models import Brand, Specification, SewingCategory, \
    PackagingCategory, Article, Order, Accessory
from sewing.serializers import BrandSerializer, SpecificationSerializer, \
    SewingCategorySerializer, PackagingCategorySerializer, ArticleSerializer, \
    OrderSerializer, AccessorySerializer


# Create your views here.





class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().order_by('name')
    serializer_class = BrandSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        qs = super().get_queryset().only('id', 'name')
        return qs

class SpecificationViewSet(viewsets.ModelViewSet):
    queryset = Specification.objects.all().order_by('name')
    serializer_class = SpecificationSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        qs = super().get_queryset().only('id', 'name')
        return qs

class SewingCategoryViewSet(viewsets.ModelViewSet):
    queryset = SewingCategory.objects.all()
    serializer_class = SewingCategorySerializer

class AccesoryViewSet(viewsets.ModelViewSet):
    queryset = Accessory.objects.all().order_by('name')
    serializer_class = AccessorySerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter]
    search_fields = ['name']

class PackagingCategoryViewSet(viewsets.ModelViewSet):
    queryset = PackagingCategory.objects.all()
    serializer_class = PackagingCategorySerializer

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().order_by('name')
    serializer_class = ArticleSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter]
    search_fields = ['name','article']

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('article__name')
    serializer_class = OrderSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter]
    search_fields = ['article__name','article__article','specification__name',
                     'comment','article__brand__name']






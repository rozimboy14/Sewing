from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.views import APIView

from sewing.models import Brand, Specification, SewingCategory, \
    PackagingCategory, Article, Order, Accessory
from sewing.serializers import BrandSerializer, SpecificationSerializer, \
    SewingCategorySerializer, PackagingCategorySerializer, ArticleSerializer, \
    OrderSerializer, AccessorySerializer


# Create your views here.





class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer

class SpecificationViewSet(viewsets.ModelViewSet):
    queryset = Specification.objects.all()
    serializer_class = SpecificationSerializer

class SewingCategoryViewSet(viewsets.ModelViewSet):
    queryset = SewingCategory.objects.all()
    serializer_class = SewingCategorySerializer

class AccesoryViewSet(viewsets.ModelViewSet):
    queryset = Accessory.objects.all()
    serializer_class = AccessorySerializer

class PackagingCategoryViewSet(viewsets.ModelViewSet):
    queryset = PackagingCategory.objects.all()
    serializer_class = PackagingCategorySerializer

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer






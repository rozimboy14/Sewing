from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from packaging.models import StockPackaging, StockPackagingVariant
from sewing.serializers import OrderSerializer


class StockPackagingVariantSerializer(serializers.ModelSerializer):
    variant_name = serializers.CharField(source='variant.name',read_only=True)
    class Meta:
        model = StockPackagingVariant
        fields = ['id','variant','variant_name','sort_1','sort_2']



class StockPackagingSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    stock_packaging_variant = StockPackagingVariantSerializer(
        source='stock_packaging_variants',  # related_name bilan mos
        many=True,
        read_only=True
    )
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    brand = serializers.CharField(source='order.article.brand.name',
                                  read_only=True)
    full_name = serializers.CharField(source='order.full_name', read_only=True)

    class Meta:
        model = StockPackaging
        fields = [
            'id', 'warehouse', 'order','brand','full_name', 'warehouse_name',
            'stock_packaging_variant', 'total_sort_1', 'total_sort_2'
        ]


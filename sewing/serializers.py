import json

from rest_framework import serializers
from sewing.models import Brand, Specification, SewingCategory, \
    PackagingCategory, Article, Order, Accessory, ArticleAccessory, \
    OrderVariant


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name','image']


class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = ['id', 'name']


class SewingCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SewingCategory
        fields = ['id', 'name', 'norm']


class PackagingCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagingCategory
        fields = ['id', 'name', 'norm']


class AccessorySerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    full_name = serializers.CharField(read_only=True)
    class Meta:
        model = Accessory
        fields = ['id', 'name', 'brand', 'brand_name', 'comment','image',
                  "type",'type_display','full_name']

    def validate(self, data):

       type_value = data.get('type')
       if not type_value:
           raise serializers.ValidationError({
               "type": f"Type maydoni bosh bo'lmasiligi kerak:"
           })
       if type_value not in dict(Accessory.TYPE_CHOICES):
           raise serializers.ValidationError("Invalid type")

       return data


class ArticleAccessorySerializer(serializers.ModelSerializer):
    accessory_name = serializers.CharField(source="accessory.full_name",
                                           read_only=True)
    accessory_brand = serializers.CharField(source="accessory.brand.name", read_only=True)

    class Meta:
        model = ArticleAccessory
        fields = ['id', 'accessory', 'accessory_name', 'accessory_brand', 'quantity']





class ArticleAccessoryInputSerializer(serializers.Serializer):
    accessory = serializers.IntegerField()
    quantity = serializers.IntegerField()

class ArticleSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    sewing_category_name = serializers.CharField(source='sewing_category.name', read_only=True)
    packaging_category_name = serializers.CharField(source='packaging_category.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    accessory_link = ArticleAccessorySerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'name', 'article', 'brand', 'brand_name', 'full_name',
            'sewing_category', 'packaging_category',
            'sewing_category_name', 'packaging_category_name',
            'accessory_link', 'image'
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        accessories_raw = request.data.get("accessories")  # bu string
        article = Article.objects.create(**validated_data)

        if accessories_raw:
            try:
                accessories_data = json.loads(accessories_raw)
                for acc in accessories_data:
                    if acc.get("accessory"):
                        ArticleAccessory.objects.create(
                            article=article,
                            accessory_id=acc["accessory"],
                            quantity=acc.get("quantity", 1)
                        )
            except Exception as e:
                raise serializers.ValidationError({"accessories": str(e)})

        return article

    def update(self, instance, validated_data):
        request = self.context.get("request")
        accessories_raw = request.data.get("accessories")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if accessories_raw is not None:
            try:
                accessories_data = json.loads(accessories_raw)
                instance.accessory_link.all().delete()
                for acc in accessories_data:
                    if acc.get("accessory"):
                        ArticleAccessory.objects.create(
                            article=instance,
                            accessory_id=acc["accessory"],
                            quantity=acc.get("quantity", 1)
                        )
            except Exception as e:
                raise serializers.ValidationError({"accessories": str(e)})

        return instance


class OrderVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderVariant
        fields = ['id','order','name']

class OrderSerializer(serializers.ModelSerializer):
    specification_name = serializers.CharField(source='specification.name',
                                               read_only=True)
    sewing_category = serializers.CharField(
        source='article.sewing_category.name', read_only=True)
    packaging_category = serializers.CharField(
        source='article.packaging_category.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    article_name = serializers.CharField(source='article.full_name',
                                               read_only=True)
    variant_link = OrderVariantSerializer(many=True, read_only=True)
    brand_name = serializers.CharField(source='article.brand_name', read_only=True)

    accessory_link = ArticleAccessorySerializer(
        source="article.accessory_link", many=True, read_only=True
    )
    class Meta:
        model = Order
        fields = ['id','specification', 'specification_name','article_name',
                  'brand_name',
                  'article', 'quantity','comment','full_name',
                  'variant_link','accessory_link',
                  "sewing_category",'packaging_category']

    def create(self, validated_data):
        request = self.context.get("request")
        variant_raw = request.data.get("variants")
        order = Order.objects.create(**validated_data)
        if variant_raw:
            try:
                variant_data = json.loads(variant_raw)
                for var in variant_data:
                    if var.get("name"):
                        OrderVariant.objects.create(
                            order=order,
                            name=var["name"],
                        )
            except Exception as e:
                raise serializers.ValidationError({"variants": str(e)})

        return order

    def update(self, instance, validated_data):
        request = self.context.get("request")
        variant_raw = request.data.get("variants")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if variant_raw is not None:
            try:
                variant_data = json.loads(variant_raw)
                instance.variant_link.all().delete()
                for var in variant_data:
                    if var.get("name"):
                        OrderVariant.objects.create(
                            order=instance,
                            name=var["name"],
                        )
            except Exception as e:
                raise serializers.ValidationError({"variants": str(e)})

        return instance

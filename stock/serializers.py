from django.db.models import Sum
from rest_framework import serializers

from sewing.models import Order, Accessory, OrderVariant
from sewing.serializers import OrderSerializer, AccessorySerializer
from stock.models import Stock, StockEntry, TotalEntry, AccessoryStock, \
    AccessoryStockEntry, StockEntryVariant, Warehouse, StockVariant


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id','name','location']

class StockVariantSerializer(serializers.ModelSerializer):
    name =serializers.CharField(source='variant.name')
    class Meta:
        model = StockVariant
        fields =['id','stock','name','variant','quantity']
class StockSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    stock_variants= StockVariantSerializer(many=True, read_only=True)


    class Meta:
        model = Stock
        fields = ['id', 'order','warehouse','total_quantity','stock_variants']



class AccessoryStockSerializer(serializers.ModelSerializer):
    accessory =AccessorySerializer(read_only=True)

    class Meta:
        model = AccessoryStock
        fields = ['id','accessory','warehouse','total_quantity']


class OrderStockSerializer(serializers.ModelSerializer):
    stocks = StockSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "quantity", "stocks"]

class StockEntryVariantSerializer(serializers.ModelSerializer):
    variant = serializers.PrimaryKeyRelatedField(
        queryset=OrderVariant.objects.all()
    )
    variant_name = serializers.CharField(source='variant.name',read_only=True)
    class Meta:
        model = StockEntryVariant
        fields = ["id", "variant", "quantity",'variant_name']


class StockEntrySerializer(serializers.ModelSerializer):
    variants = StockEntryVariantSerializer(many=True)
    order_name = serializers.CharField(source='order.full_name', read_only=True)
    brand_name = serializers.CharField(source='order.article.brand.name', read_only=True)
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = StockEntry
        fields = ["id",'total_entry', "order", 'order_name', 'variants',
                  "date", 'brand_name', 'total_quantity']

    def get_total_quantity(self, obj):
        return obj.variants.aggregate(total=Sum('quantity'))['total'] or 0

    def create(self, validated_data):
        variants_data = validated_data.pop("variants")
        stock_entry = StockEntry.objects.create(**validated_data)
        for v in variants_data:
            StockEntryVariant.objects.create(stock_entry=stock_entry, **v)
        return stock_entry

    def update(self, instance, validated_data):
        variants_data = validated_data.pop("variants", None)

        # oddiy maydonlarni yangilash
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if variants_data is not None:
            for v in variants_data:
                variant = v.get("variant")
                quantity = v.get("quantity")

                # agar variant obyekt bo‘lsa → id olamiz
                if isinstance(variant, OrderVariant):
                    variant_id = variant.id
                else:
                    variant_id = variant

                entry_variant, created = StockEntryVariant.objects.update_or_create(
                    stock_entry=instance,
                    variant_id=variant_id,
                    defaults={"quantity": quantity}
                )

        return instance
class StockEntryBulkSerializer(serializers.Serializer):
    total_entry = serializers.PrimaryKeyRelatedField(queryset=TotalEntry.objects.all())
    orders = serializers.ListField()

    def create(self, validated_data):
        total_entry = validated_data["total_entry"]
        orders = validated_data["orders"]

        created_entries = []

        for order_data in orders:
            order_id = order_data["order"]
            variants = order_data["variants"]

            # bitta StockEntry yaratamiz
            entry = StockEntry.objects.create(
                total_entry=total_entry,
                order_id=order_id,

            )

            # barcha variantlarni shu StockEntry bilan bog‘laymiz
            for v in variants:
                StockEntryVariant.objects.create(
                    stock_entry=entry,
                    variant_id=v["variant"],
                    quantity=v["quantity"]
                )

            created_entries.append(entry)

        return created_entries


class AccessoryStockEntrySerializer(serializers.ModelSerializer):
    accessory_id = serializers.PrimaryKeyRelatedField(
        queryset=Accessory.objects.all(),
        source='accessory',
        write_only=True
    )
    brand_id = serializers.CharField(source='accessory.brand.id',
                                     read_only=True)
    brand_name = serializers.CharField(source='accessory.brand.name',
                                       read_only=True)
    accessory =AccessorySerializer( read_only=True)
    accessory_name = serializers.CharField(source='accessory.name',
                                           read_only=True)
    accessory_comment = serializers.CharField(source='accessory.comment', read_only=True)
    type_display = serializers.CharField(source='accessory.type_display', read_only=True
                                        )
    class Meta:
        model = AccessoryStockEntry
        fields = ['id','accessory_id','accessory','quantity','date',
                  'accessory_comment','type_display','accessory_name',
                  'total_entry','brand_id','brand_name']



class TotalEntrySerializer(serializers.ModelSerializer):
    stock_entries = StockEntrySerializer(many=True, read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    accessory_stock_entries = AccessoryStockEntrySerializer(many=True, read_only=True)
    total_quantity = serializers.SerializerMethodField()
    total_quantity_accessory = serializers.SerializerMethodField()
    created_date = serializers.DateTimeField(format="%d.%m.%Y %H:%M",
                                             required=False)
    class Meta:
        model = TotalEntry
        fields = ['id','created_date','comment','warehouse',
                  'warehouse_name','stock_entries',
                  'accessory_stock_entries','total_quantity',
                  'total_quantity_accessory','confirmed']

    def get_total_quantity(self, obj):
        return StockEntryVariant.objects.filter(
            stock_entry__total_entry=obj).aggregate(
            total=Sum('quantity')
        )['total'] or 0

    def get_total_quantity_accessory(self, obj):
        return AccessoryStockEntry.objects.filter(total_entry=obj).aggregate(
            total=Sum('quantity')
        )['total'] or 0

class CategoryStockSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    total_quantity = serializers.IntegerField()


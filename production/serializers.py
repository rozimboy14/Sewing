
from production.models import (
    ProductionLine, ProductionReport,
    NormCategory, ProductionNorm, ProductionCategorySummary,
    MonthPlaning, MonthPlaningOrder
)
from sewing.models import Order
from sewing.serializers import OrderSerializer
from services.stock_service import   NormCategoryService, \
    check_stock_variant_bulk
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from production.models import Daily, Line, LineOrders



class ProductionLineSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source='warehouse.name',
                                           read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = ProductionLine
        fields = ['id', 'warehouse', 'name', 'full_name', 'warehouse_name']


# -------------------------
class LineOrdersSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="order.full_name", read_only=True)

    class Meta:
        model = LineOrders
        fields = ['id', 'order_line', 'order', 'sort_1', 'sort_2',
                  'defect_quantity', 'full_name']

    def validate(self, attrs):
        # yangi qiymatlarni olamiz
        new_sort_1 = attrs.get("sort_1", getattr(self.instance, "sort_1", 0))
        new_sort_2 = attrs.get("sort_2", getattr(self.instance, "sort_2", 0))
        new_defect = attrs.get("defect_quantity", getattr(self.instance, "defect_quantity", 0))
        new_total = (new_sort_1 or 0) + (new_sort_2 or 0) + (new_defect or 0)

        # eski qiymatlarni olamiz
        old_total = 0
        if self.instance:
            old_total = (
                (self.instance.sort_1 or 0)
                + (self.instance.sort_2 or 0)
                + (self.instance.defect_quantity or 0)
            )

        # farqni topamiz
        diff = new_total - old_total

        # faqat ijobiy farqni tekshiramiz
        if diff > 0:
            line_order = self.instance or LineOrders(**attrs)
            try:
                # ✅ faqat diff miqdorini tekshiramiz
                check_stock_variant_bulk(line_order, diff)
            except ValidationError as e:
                raise serializers.ValidationError(e.detail)

        return attrs

class LineSerializer(serializers.ModelSerializer):
    order_line = LineOrdersSerializer(many=True, read_only=True)
    line = serializers.CharField(read_only=True)

    class Meta:
        model = Line
        fields = ['id', 'line_daily', 'line', 'production_norm',
                  'order_line', 'sort_1', 'sort_2', 'defect_quantity']


class DailySerializer(serializers.ModelSerializer):
    lines = LineSerializer(many=True, read_only=True)
    is_weekend = serializers.SerializerMethodField()

    class Meta:
        model = Daily
        fields = ['id', 'production_report', 'date', 'lines', 'sort_1',
                  'sort_2', 'defect_quantity', 'is_weekend']

    def get_is_weekend(self, obj):
        """
        Shanba yoki Yakshanba bo‘lsa True qaytaradi
        """
        # weekday(): 0=Monday, 5=Saturday, 6=Sunday
        return obj.date.weekday() >= 6


class NormCategorySerializer(serializers.ModelSerializer):
    order_name = serializers.CharField(source='order.full_name',
                                       read_only=True)

    order_detail = OrderSerializer(source='order', read_only=True)
    order_variant_name = serializers.CharField(source='order_variant.name',
                                               read_only=True)

    class Meta:
        model = NormCategory
        fields = ['id', 'production_norm', 'order', 'order_variant',
                  'order_name',
                  'norm', 'total_sort_1', 'total_sort_2', 'total_defect'
            , 'order_variant_name', 'order_detail']

    def validate(self, attrs):
        production_norm = attrs.get("production_norm") or getattr(
            self.instance,
            "production_norm",
            None)
        order_variant = attrs.get("order_variant") or getattr(self.instance,
                                                              "order_variant",
                                                              None)

        if NormCategory.objects.filter(production_norm=production_norm,
                                       order_variant=order_variant).exclude(
            id=getattr(self.instance, "id", None)).exists():
            raise serializers.ValidationError(
                {"order": "Bu Model allaqachon mavjud!"})
        return attrs


class ProductionNormSerializer(serializers.ModelSerializer):
    norm_category = NormCategorySerializer(many=True, read_only=True)
    line_name = serializers.CharField(source='line.full_name', read_only=True)
    total_norm = serializers.SerializerMethodField()

    class Meta:
        model = ProductionNorm
        fields = ['id', 'line', 'line_name', 'norm_category', 'total_norm',
                  'production_report', 'total_sort_1', 'total_sort_2',
                  'total_defect']

    def get_total_norm(self, obj):
        return sum(
            nc.norm for nc in obj.norm_category.all() if nc.norm is not None)


class ProductionCategorySummarySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name',
                                          read_only=True)

    class Meta:
        model = ProductionCategorySummary
        fields = ['id', 'production_report', 'category', 'category_name',
                  'norm', 'actual']


class ProductionReportSerializer(serializers.ModelSerializer):
    daily_report = DailySerializer(many=True, read_only=True)
    production_norm = ProductionNormSerializer(many=True, read_only=True)
    category_summaries = ProductionCategorySummarySerializer(many=True,
                                                             read_only=True)
    percent_done = serializers.SerializerMethodField()
    day_norm = serializers.SerializerMethodField()
    year_display = serializers.SerializerMethodField()
    month_display = serializers.SerializerMethodField()

    class Meta:
        model = ProductionReport
        fields = ['id', 'warehouse', 'year', 'month', 'total_sort_1',
                  'total_sort_2', 'total_defect',
                  'total_norm', 'month_display', 'year_display',
                  'category_summaries', 'production_norm',
                  'daily_report', 'percent_done', 'day_norm', 'comment']

    def get_percent_done(self, obj):
        total_quantity = obj.total_sort_1 or 0 + obj.total_sort_2 or 0
        total_norm = obj.total_norm or 0
        if not total_norm:
            return 0
        return round((total_quantity / total_norm) * 100, 1)

    def get_day_norm(self, obj):
        try:
            day = int(obj.day)
        except (TypeError, ValueError):
            return 0
        if day == 0:
            return 0
        return round(obj.total_norm / day)

    def get_month_display(self, obj):
        return obj.get_month_display()

    def get_year_display(self, obj):
        return str(obj.year)


class ProductionNormBulkSerializer(serializers.Serializer):
    production_report = serializers.IntegerField()
    line = serializers.ListField(
        child=serializers.IntegerField()
    )

    def create(self, validated_data):
        # production_report id → instance
        try:
            production_report = ProductionReport.objects.get(
                pk=validated_data["production_report"])
        except ProductionReport.DoesNotExist:
            raise serializers.ValidationError(
                {"production_report": "Bunday report yo‘q"})

        line_ids = validated_data["line"]
        objs = []

        for line_id in line_ids:
            try:
                line_instance = ProductionLine.objects.get(pk=line_id)
            except ProductionLine.DoesNotExist:
                raise serializers.ValidationError(
                    {"line": f"Line id={line_id} topilmadi"})

            # Service chaqirishda instance yuborish
            obj = NormCategoryService.create_norm_category(
                production_report=production_report,
                line=line_instance,  # ✅ instance
            )
            objs.append(obj)

        return objs


class MonthPlaningOrderSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    order_detail = OrderSerializer(source="order", read_only=True)
    percent_done = serializers.SerializerMethodField()

    class Meta:
        model = MonthPlaningOrder
        fields = ['id', 'stock_quantity', 'month_planing', 'order',
                  'order_detail',
                  'planed_quantity', 'fact_quantity', 'norm_quantity',
                  'percent_done']

    def get_percent_done(self, obj):
        fact_quantity = obj.fact_quantity or 0
        planed_quantity = obj.planed_quantity or 0

        if not planed_quantity:  # nolga bo‘lishdan saqlanish
            return 0

        return round((fact_quantity / planed_quantity) * 100, 1)


class MonthPlaningSerializers(serializers.ModelSerializer):
    month_planing_orders = MonthPlaningOrderSerializer(many=True,
                                                       read_only=True,
                                                       source='month_planing_order')
    year_display = serializers.SerializerMethodField()
    month_display = serializers.SerializerMethodField()
    warehouse_name = serializers.CharField(source='warehouse.name',
                                           read_only=True)
    percent_done = serializers.SerializerMethodField()

    class Meta:
        model = MonthPlaning
        fields = ['id', 'warehouse', 'warehouse_name', 'month', 'year',
                  'year_display',
                  'month_display',
                  'day_planing',
                  'planing_quantity',
                  'fact_quantity',
                  'percent_done',
                  'comment', 'month_planing_orders']

    def get_month_display(self, obj):
        return obj.get_month_display()

    def get_year_display(self, obj):
        return str(obj.year)

    def get_percent_done(self, obj):
        fact_quantity = obj.fact_quantity or 0
        planed_quantity = obj.planing_quantity or 0

        if not planed_quantity:  # nolga bo‘lishdan saqlanish
            return 0

        return round((fact_quantity / planed_quantity) * 100, 1)

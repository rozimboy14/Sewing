from collections import defaultdict

from django.db.models.aggregates import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from weasyprint import HTML

from packaging.models import StockPackaging, StockPackagingVariant
from packaging.serializers import StockPackagingSerializer, \
    StockPackagingVariantSerializer
from production.models import ProductionLine
from sewing.models import PackagingCategory, Brand
from stock.models import Warehouse, Stock


# Create your views here.

class StockPackagingViewSet(viewsets.ModelViewSet):
    queryset = StockPackaging.objects.all()
    serializer_class = StockPackagingSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'order__article__brand_id': ['exact'],
        'order__article__packaging_category_id': ['exact'],
        'warehouse_id': ['exact'],
    }

    @action(detail=False, methods=['get'], url_path='export-pdf')
    def export_stock_pdf(self, request):

        warehouse_id = request.query_params.get('warehouse_id')
        warehouse_name = ""
        queryset = self.get_queryset()
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
                warehouse_name = warehouse.name
            except Warehouse.DoesNotExist:
                warehouse_name = f"ID {warehouse_id} not found"

        queryset = queryset.prefetch_related(
            'stock_packaging_variants__variant',
            'order__article__brand',
            'order__specification'
        ).order_by(
            'order__article__brand__name',
            'order__specification__name'
        )

        # brand -> specification -> order
        brand_data = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list)))
        order_totals = defaultdict(lambda: defaultdict(
            lambda: defaultdict(lambda: {"sort_1": 0, "sort_2": 0})))
        specification_totals = defaultdict(
            lambda: defaultdict(lambda: {"sort_1": 0, "sort_2": 0}))
        brand_order_totals = defaultdict(lambda: {"sort_1": 0, "sort_2": 0})

        brand_rowspans = defaultdict(int)
        specification_rowspans = defaultdict(lambda: defaultdict(int))
        total_sort_1 = 0
        total_sort_2 = 0
        for stock in queryset:
            brand_name = stock.order.article.brand.name
            specification_name = stock.order.specification.name
            order_name = stock.order.full_name
            variant_count = 0
            for sv in stock.stock_packaging_variants.all():
                brand_data[brand_name][specification_name][order_name].append({
                    "variant_id": sv.variant.id,
                    "variant_name": sv.variant.name,
                    "sort_1": sv.sort_1,
                    "sort_2": sv.sort_2
                })

                order_totals[brand_name][specification_name][order_name][
                    "sort_1"] += sv.sort_1
                order_totals[brand_name][specification_name][order_name][
                    "sort_2"] += sv.sort_2

                specification_totals[brand_name][specification_name][
                    "sort_1"] += sv.sort_1
                specification_totals[brand_name][specification_name][
                    "sort_2"] += sv.sort_2

                brand_order_totals[brand_name]["sort_1"] += sv.sort_1
                brand_order_totals[brand_name]["sort_2"] += sv.sort_2
                total_sort_1 += sv.sort_1
                total_sort_2 += sv.sort_2
                # rowspans hisoblash
                brand_rowspans[brand_name] += 1
                specification_rowspans[brand_name][specification_name] += 1

            # har order bo‘yicha qo‘shiladigan "Итого по заказу" qatori
            brand_rowspans[brand_name] += 2
            specification_rowspans[brand_name][specification_name] += 1

        html_string = render_to_string(
            'StockPackage/stock_package_template.html', {
                "warehouse_name": warehouse_name,
                'grouped_orders': {
                    brand: {spec: dict(orders) for spec, orders in
                            specs.items()}
                    for brand, specs in brand_data.items()
                },
                'order_totals': {
                    brand: {spec: dict(orders) for spec, orders in
                            specs.items()}
                    for brand, specs in order_totals.items()
                },
                'specification_totals': {
                    brand: dict(specs) for brand, specs in
                    specification_totals.items()
                },
                'brand_order_totals': dict(brand_order_totals),
                'brand_rowspans': dict(brand_rowspans),
                'specification_rowspans': {
                    brand: dict(specs) for brand, specs in
                    specification_rowspans.items()
                },
               'total_sort_1':total_sort_1,
                'total_sort_2':total_sort_2
            })

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="warehouse_'
            f'{warehouse_id or "all"}_stock_package.pdf"'
        )

        HTML(string=html_string).write_pdf(response)
        return response
    @action(detail=False, methods=['get'], url_path='export-brand-pdf')
    def export_stock_brand_pdf(self, request):
        brand_id = request.query_params.get('brand_id')
        warehouse_id = request.query_params.get('warehouse_id')
        warehouse_name = ""
        brand_name = ""
        queryset = self.get_queryset()
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
                warehouse_name = warehouse.name
            except Warehouse.DoesNotExist:
                warehouse_name = f"ID {warehouse_id} not found"
        if brand_id:
            queryset = queryset.filter(order__article__brand_id=brand_id)
            try:
                brand = Brand.objects.get(id=brand_id)
                brand_name = brand.name
            except Warehouse.DoesNotExist:
                brand_name = f"ID {brand_id} not found"

        queryset = queryset.prefetch_related(
            'stock_packaging_variants__variant',
            'order__article__brand',
            'order__specification'
        ).order_by(
            'order__article__brand__name',
            'order__specification__name'
        )


        # brand -> specification -> order
        brand_data = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list)))
        order_totals = defaultdict(lambda: defaultdict(
            lambda: defaultdict(lambda: {"sort_1": 0, "sort_2": 0})))
        specification_totals = defaultdict(
            lambda: defaultdict(lambda: {"sort_1": 0, "sort_2": 0}))
        brand_order_totals = defaultdict(lambda: {"sort_1": 0, "sort_2": 0})

        specification_rowspans = defaultdict(lambda: defaultdict(int))
        total_sort_1 = 0
        total_sort_2 = 0



        for stock in queryset:
            brand_name = stock.order.article.brand.name
            specification_name = stock.order.specification.name
            order_name = stock.order.full_name
            variant_count = 0
            for sv in stock.stock_packaging_variants.all():
                brand_data[brand_name][specification_name][order_name].append({
                    "variant_id": sv.variant.id,
                    "variant_name": sv.variant.name,
                    "sort_1": sv.sort_1,
                    "sort_2": sv.sort_2
                })

                order_totals[brand_name][specification_name][order_name][
                    "sort_1"] += sv.sort_1
                order_totals[brand_name][specification_name][order_name][
                    "sort_2"] += sv.sort_2

                specification_totals[brand_name][specification_name][
                    "sort_1"] += sv.sort_1
                specification_totals[brand_name][specification_name][
                    "sort_2"] += sv.sort_2

                brand_order_totals[brand_name]["sort_1"] += sv.sort_1
                brand_order_totals[brand_name]["sort_2"] += sv.sort_2
                total_sort_1 += sv.sort_1
                total_sort_2 += sv.sort_2
                variant_count += 1

                # rowspans hisoblash

                specification_rowspans[brand_name][specification_name] += 1

            # har order bo‘yicha qo‘shiladigan "Итого по заказу" qatori
            specification_rowspans[brand_name][specification_name] += 1

        html_string = render_to_string(
            'StockPackage/stock_package_brand_template.html', {
            "warehouse_name": warehouse_name,
            "brand_name":brand_name,
            'grouped_orders': {
                brand: {spec: dict(orders) for spec, orders in specs.items()}
                for brand, specs in brand_data.items()
            },
            'order_totals': {
                brand: {spec: dict(orders) for spec, orders in specs.items()}
                for brand, specs in order_totals.items()
            },
            'specification_totals': {
                brand: dict(specs) for brand, specs in
                specification_totals.items()
            },
            'brand_order_totals': dict(brand_order_totals),
            'specification_rowspans': {
                brand: dict(specs) for brand, specs in
                specification_rowspans.items()
            },
                'total_sort_1': total_sort_1,
                'total_sort_2': total_sort_2
        })

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="warehouse_{warehouse_id or "all"}_stock.pdf"'
        )

        HTML(string=html_string).write_pdf(response)
        return response

class StockPackagingVariantViewSet(viewsets.ModelViewSet):
    queryset = StockPackagingVariant.objects.all()
    serializer_class = StockPackagingVariantSerializer


class StockPackagingBrandListView(APIView):
    def get(self, request):
        warehouse_id = request.query_params.get("warehouse_id")
        if not warehouse_id:
            return Response({"detail": "warehouse_id is required"}, status=400)

        # Omborni olish
        warehouse = Warehouse.objects.filter(id=warehouse_id).first()
        if not warehouse:
            return Response({"detail": "Warehouse not found"}, status=404)

        # 🔹 Brandlar faqat shu ombordan olinadi
        brands = (
            StockPackaging.objects
            .filter(warehouse=warehouse)
            .values(
                'order__article__brand',
                'order__article__brand__name',
                'order__article__brand__image'
            )
            .annotate(sort_1=Sum('stock_packaging_variants__sort_1'),
                      sort_2=Sum('stock_packaging_variants__sort_2'))
            .order_by('order__article__brand__name')
        )

        brand_list = []
        for brand in brands:
            brand_id = brand['order__article__brand']

            # 🔹 Har bir brand ichidagi spetsifikatsiyalar
            specs = (
                StockPackaging.objects
                .filter(order__article__brand_id=brand_id, warehouse=warehouse)
                .values(
                    'order__specification',
                    'order__specification__name'
                )
                .annotate(sort_1=Sum('stock_packaging_variants__sort_1'),
                          sort_2=Sum(
                              'stock_packaging_variants__sort_2'))
                .order_by('order__specification__name')
            )

            brand_list.append({
                'brand_id': brand_id,
                'brand_name': brand['order__article__brand__name'],
                'brand_image': (
                    request.build_absolute_uri(
                        f"/media/{brand['order__article__brand__image']}")
                    if brand['order__article__brand__image'] else None
                ),
                'sort_1': brand['sort_1'],
                'sort_2': brand['sort_2'],
                'specifications': [
                    {
                        'spec_id': spec['order__specification'],
                        'spec_name': spec['order__specification__name'],
                        'sort_1': spec['sort_1'],
                        'sort_2': spec['sort_2']
                    }
                    for spec in specs
                ]
            })
        total_sort_1 = sum(c["sort_1"] for c in brand_list)
        total_sort_2 = sum(c["sort_2"] for c in brand_list)
        result = {
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "warehouse_location": warehouse.location,
            "brands": brand_list,
            "total_sort_1": total_sort_1,
            "total_sort_2": total_sort_2,
        }

        return Response(result)


class StockCategoryViewSet(APIView):
    def get(self, request):
        warehouse_id = request.query_params.get("warehouse_id")
        if not warehouse_id:
            return Response({"detail": "warehouse_id is required"}, status=400)

        warehouse = Warehouse.objects.filter(id=warehouse_id).first()
        if not warehouse:
            return Response({"detail": "Warehouse not found"}, status=404)

        # Omborda mavjud bo‘lgan kategoriyalarni olish
        data = (
            StockPackaging.objects.filter(warehouse=warehouse)
            .values("order__article__packaging_category")
            .annotate(sort_1=Sum("stock_packaging_variants__sort_1"),
                      sort_2=Sum("stock_packaging_variants__sort_2"))
        )
        stock_map = {
            s["order__article__packaging_category"]: {
                "sort_1": s["sort_1"],
                "sort_2": s["sort_2"],
            }
            for s in data
        }

        # Hamma kategoriyalarni olish
        all_categories = PackagingCategory.objects.all()
        category_list = []
        for cat in all_categories:
            stock_data = stock_map.get(cat.id, {"sort_1": 0, "sort_2": 0})
            sort_1 = stock_data["sort_1"]
            sort_2 = stock_data["sort_2"]
            norm = float(cat.norm) if cat.norm else 1.0

            category_list.append({
                "category_id": cat.id,
                "category_name": cat.name,
                "sort_1": sort_1,
                "sort_2": sort_2,
                "norm": norm,

            })

        result = {
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "warehouse_location": warehouse.location,
            "category_list": category_list,

        }

        return Response(result)

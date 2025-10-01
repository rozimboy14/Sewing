import math
from collections import defaultdict
from gc import get_objects

from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from weasyprint import HTML
from django.template.loader import get_template, render_to_string

from django_filters.rest_framework import DjangoFilterBackend

from production.models import ProductionLine
from sewing.models import Brand, SewingCategory
from stock.models import (Stock, StockEntry, TotalEntry, AccessoryStockEntry,
                          AccessoryStock, Warehouse)
from stock.serializers import StockSerializer, TotalEntrySerializer, \
    StockEntrySerializer, AccessoryStockEntrySerializer, \
    AccessoryStockSerializer, StockEntryBulkSerializer, WarehouseSerializer
from rest_framework.views import APIView
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import cm


# Create your views here.
class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer


class StockView(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'order__article__brand_id': ['exact'],
        'order__article__sewing_category_id': ['exact'],
        'warehouse_id': ['exact'],
    }

    @action(detail=False, methods=['get'], url_path='export-pdf')
    def export_stock_pdf(self, request):
        brand_id = request.query_params.get('brand_id')
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
        if brand_id:
            queryset = queryset.filter(order__article__brand_id=brand_id)

        queryset = queryset.prefetch_related(
            'stock_variants__variant',
            'order__article__brand',
            'order__specification'
        ).order_by(
            'order__article__brand__name',
            'order__specification__name'
        )


        # brand -> specification -> order
        brand_data = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list)))
        order_totals = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int)))
        specification_totals = defaultdict(lambda: defaultdict(int))
        brand_order_totals = defaultdict(int)

        brand_rowspans = defaultdict(int)
        specification_rowspans = defaultdict(lambda: defaultdict(int))

        for stock in queryset:
            brand_name = stock.order.article.brand.name
            specification_name = stock.order.specification.name
            order_name = stock.order.full_name
            variant_count = 0
            for sv in stock.stock_variants.all():
                brand_data[brand_name][specification_name][order_name].append({
                    "variant_id": sv.variant.id,
                    "variant_name": sv.variant.name,
                    "quantity": sv.quantity
                })

                order_totals[brand_name][specification_name][
                    order_name] += sv.quantity
                specification_totals[brand_name][
                    specification_name] += sv.quantity
                brand_order_totals[brand_name] += sv.quantity
                variant_count += 1

                # rowspans hisoblash
                brand_rowspans[brand_name] += 1
                specification_rowspans[brand_name][specification_name] += 1

            # har order bo‘yicha qo‘shiladigan "Итого по заказу" qatori
            brand_rowspans[brand_name] += 2
            specification_rowspans[brand_name][specification_name] += 1

        html_string = render_to_string('stock/stock_template.html', {
            "warehouse_name": warehouse_name,
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
            'brand_rowspans': dict(brand_rowspans),
            'specification_rowspans': {
                brand: dict(specs) for brand, specs in
                specification_rowspans.items()
            }
        })

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="warehouse_{warehouse_id or "all"}_stock.pdf"'
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
            'stock_variants__variant',
            'order__article__brand',
            'order__specification'
        ).order_by(
            'order__article__brand__name',
            'order__specification__name'
        )


        # brand -> specification -> order
        brand_data = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list)))
        order_totals = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int)))
        specification_totals = defaultdict(lambda: defaultdict(int))
        brand_order_totals = defaultdict(int)


        specification_rowspans = defaultdict(lambda: defaultdict(int))

        for stock in queryset:
            brand_name = stock.order.article.brand.name
            specification_name = stock.order.specification.name
            order_name = stock.order.full_name
            variant_count = 0
            for sv in stock.stock_variants.all():
                brand_data[brand_name][specification_name][order_name].append({
                    "variant_id": sv.variant.id,
                    "variant_name": sv.variant.name,
                    "quantity": sv.quantity
                })

                order_totals[brand_name][specification_name][
                    order_name] += sv.quantity
                specification_totals[brand_name][
                    specification_name] += sv.quantity
                brand_order_totals[brand_name] += sv.quantity
                variant_count += 1

                # rowspans hisoblash

                specification_rowspans[brand_name][specification_name] += 1

            # har order bo‘yicha qo‘shiladigan "Итого по заказу" qatori
            specification_rowspans[brand_name][specification_name] += 1

        html_string = render_to_string('stock/stock_brand_template.html', {
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
            }
        })

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="warehouse_{warehouse_id or "all"}_stock.pdf"'
        )

        HTML(string=html_string).write_pdf(response)
        return response
class AccessoryStockView(viewsets.ModelViewSet):
    queryset = AccessoryStock.objects.all()
    serializer_class = AccessoryStockSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        warehouse_id = self.request.query_params.get('warehouse_id')
        brand_id = self.request.query_params.get('brand_id')
        type_name = self.request.query_params.get('type_name')
        if brand_id:
            queryset = queryset.filter(accessory__brand_id=brand_id)

        if type_name:
            queryset = queryset.filter(
                accessory__name__icontains=type_name)
        if warehouse_id:
            queryset = queryset.filter(
                warehouse=warehouse_id)

        return queryset

    @action(detail=False, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request):
        type_name = request.query_params.get('type_name')
        brand_id = request.query_params.get('brand_id')
        warehouse_id = request.query_params.get('warehouse_id')
        queryset = self.get_queryset()
        total_quantity = queryset.aggregate(total=Sum('total_quantity'))[
                             'total'] or 0


        context = {
            'queryset': queryset,
            'type_name': type_name,
            'brand_id': brand_id,
            'warehouse_id':warehouse_id,
            'total_quantity': total_quantity,
        }

        template = get_template('stock/accessory_stock_template.html')
        html_string = template.render(context)

        # WeasyPrint orqali PDF yaratish

        html = HTML(string=html_string)

        response = HttpResponse(content_type='application/pdf')
        filename = f"{warehouse_id or 'all'}-{type_name or 'all'}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        html.write_pdf(response)  # WeasyPrint ishlaydi

        return response
class TotalEntryView(viewsets.ModelViewSet):
    queryset = TotalEntry.objects.all()
    serializer_class = TotalEntrySerializer

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm_entry(self, request, pk=None):
        entry = self.get_object()

        if entry.confirmed:
            return Response(
                {"detail": "Bu kirim allaqachon tasdiqlangan."},
                status=status.HTTP_400_BAD_REQUEST
            )

        entry.confirm()
        return Response(
            {"detail": "Kirim muvaffaqiyatli tasdiqlandi."},
            status=status.HTTP_200_OK
        )

class AccessoryStockEntryView(viewsets.ModelViewSet):
    queryset = AccessoryStock.objects.all()
    serializer_class = AccessoryStockEntrySerializer

    def get_queryset(self):
        queryset = AccessoryStockEntry.objects.all()
        total_entry_id = self.request.query_params.get('total_entry_id')
        if total_entry_id:
            queryset = queryset.filter(total_entry_id=total_entry_id)
        return queryset

    # views.py
    def create(self, request, *args, **kwargs):
        data = request.data

        # Bir nechta yozuv kelsa
        if isinstance(data, list):
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                for item in serializer.validated_data:
                    obj = AccessoryStockEntry(
                        total_entry=item['total_entry'],
                        accessory=item['accessory'],
                        quantity=item['quantity']
                    )
                    obj.save()  # bu yerda sening save() methoding ishlaydi

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # Bitta yozuv kelsa
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class StockEntryView(viewsets.ModelViewSet):
    queryset = StockEntry.objects.all()
    serializer_class = StockEntrySerializer

    def get_queryset(self):
        queryset = StockEntry.objects.all()
        total_entry_id = self.request.query_params.get('total_entry_id')
        if total_entry_id:
            queryset = queryset.filter(total_entry_id=total_entry_id)
        return queryset

    # views.py
    def create(self, request, *args, **kwargs):
        data = request.data

        # Bir nechta yozuv kelsa
        if isinstance(data, list):
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                for item in serializer.validated_data:
                    obj = StockEntry(
                        total_entry=item['total_entry'],
                        order=item['order'],
                        quantity=item['quantity']
                    )
                    obj.save()  # bu yerda sening save() methoding ishlaydi

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # Bitta yozuv kelsa
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

def total_entry_pdf(request, total_entry_id):
    total_entry_instance = get_object_or_404(
        TotalEntry.objects.prefetch_related(
            'stock_entries__variants__variant',
            'accessory_stock_entries__accessory__brand'
        ),
        id=total_entry_id
    )
    serializer = TotalEntrySerializer(total_entry_instance)
    total_entry_data = serializer.data

    grouped_accessories = defaultdict(dict)  # brand -> {accessory_id: entry}
    brand_totals = defaultdict(int)

    for entry in total_entry_data['accessory_stock_entries']:
        brand = entry['brand_name']
        acc_id = entry['accessory']['id']

        if acc_id not in grouped_accessories[brand]:
            grouped_accessories[brand][acc_id] = entry.copy()
        else:
            grouped_accessories[brand][acc_id]['quantity'] += entry['quantity']

        brand_totals[brand] += entry['quantity']

    # dict -> list qilib o‘tkazamiz (template uchun qulay bo‘ladi)
    grouped_accessories = {
        brand: list(accessories.values())
        for brand, accessories in grouped_accessories.items()
    }

    grouped_orders = defaultdict(lambda: defaultdict(list))
    order_totals = defaultdict(lambda: defaultdict(int))
    brand_rowspans = defaultdict(int)
    brand_order_totals = defaultdict(int)
    # order darajasida variantlarni yig‘ish uchun
    order_variant_map = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int)))

    for stock_entry in total_entry_data['stock_entries']:
        brand_name = stock_entry['brand_name']
        order_name = stock_entry['order_name']

        for variant_entry in stock_entry['variants']:
            key = (variant_entry['variant'], variant_entry['variant_name'])
            order_variant_map[brand_name][order_name][key] += variant_entry[
                'quantity']

    # endi yig‘ilgan variantlarni qo‘shamiz
    for brand_name, orders in order_variant_map.items():

        for order_name, variants in orders.items():

            for (variant_id, variant_name), qty in variants.items():
                grouped_orders[brand_name][order_name].append({
                    "variant": variant_id,
                    "variant_name": variant_name,
                    "quantity": qty
                })
                order_totals[brand_name][order_name] += qty
                brand_rowspans[brand_name] += 1
            brand_rowspans[brand_name] += 1
    for brand_name, orders in order_totals.items():
        for order_name, total_qty in orders.items():
            brand_order_totals[brand_name] += total_qty
    grouped_accessories = dict(grouped_accessories)
    brand_totals = dict(brand_totals)

    grouped_orders = {k: dict(v) for k, v in grouped_orders.items()}
    order_totals = {k: dict(v) for k, v in order_totals.items()}

    html_string = render_to_string('stock_entry_template.html', {
        'total_entry': total_entry_data,
        'grouped_accessories': grouped_accessories,
        'brand_totals': brand_totals,
        'grouped_orders': grouped_orders,
        'order_totals': order_totals,
        'brand_rowspans': brand_rowspans,
        'brand_order_totals': brand_order_totals,

    })

    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = f'attachment; filename="total_entry_{total_entry_id}.pdf"'

    HTML(string=html_string).write_pdf(response)

    return response


class StockCategoryViewSet(APIView):
    def get(self, request):
        warehouse_id = request.query_params.get("warehouse_id")
        if not warehouse_id:
            return Response({"detail": "warehouse_id is required"}, status=400)

        warehouse = Warehouse.objects.filter(id=warehouse_id).first()
        if not warehouse:
            return Response({"detail": "Warehouse not found"}, status=404)

        line_count = ProductionLine.objects.filter(warehouse=warehouse).count() or 1

        # Omborda mavjud bo‘lgan kategoriyalarni olish
        data = (
            Stock.objects.filter(warehouse=warehouse)
            .values("order__article__sewing_category")
            .annotate(total_quantity=Sum("stock_variants__quantity"))
        )
        stock_map = {
            s["order__article__sewing_category"]: s["total_quantity"]
            for s in data
        }

        # Hamma kategoriyalarni olish
        all_categories = SewingCategory.objects.all()
        category_list = []
        for cat in all_categories:
            total_qty = stock_map.get(cat.id, 0)  # mavjud bo‘lmasa 0
            norm = float(cat.norm) if cat.norm else 1.0
            category_day = total_qty / (norm * line_count) if total_qty else 0
            category_list.append({
                "category_id": cat.id,
                "category_name": cat.name,
                "total_quantity": total_qty,
                "norm": norm,
                "line_count": line_count,
                "category_day": round(category_day, 2),
            })

        critical_day = max((c["category_day"] for c in category_list), default=0)
        critical_total_day = sum(math.ceil(c["category_day"]) for c in category_list)
        total_quantity = sum(c["total_quantity"] for c in category_list)

        throughput_total = sum(
            math.ceil(c["total_quantity"] / c["norm"])
            for c in category_list if c["norm"] > 0
        )
        throughput_day = throughput_total / line_count

        result = {
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "warehouse_location": warehouse.location,
            "line_count": line_count,
            "category_list": category_list,
            "critical_day": round(critical_day, 2),
            "critical_total_day": round(critical_total_day, 2),
            "throughput_estimate_day": math.ceil(throughput_day),
            "total_quantity": total_quantity,
        }

        return Response(result)

class StockBrandListView(APIView):
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
            Stock.objects
            .filter(warehouse=warehouse)
            .values(
                'order__article__brand',
                'order__article__brand__name',
                'order__article__brand__image'
            )
            .annotate(total_quantity=Sum('stock_variants__quantity'))
            .order_by('order__article__brand__name')
        )

        brand_list = []
        for brand in brands:
            brand_id = brand['order__article__brand']

            specs = (
                Stock.objects
                .filter(order__article__brand_id=brand_id, warehouse=warehouse)
                .values(
                    'order__specification',
                    'order__specification__name'
                )
                .annotate(total_quantity=Sum('stock_variants__quantity'))
                .order_by('order__specification__name')
            )

            brand_list.append({
                'brand_id': brand_id,
                'brand_name': brand['order__article__brand__name'],
                'brand_image': (
                    request.build_absolute_uri(f"/media/{brand['order__article__brand__image']}")
                    if brand['order__article__brand__image'] else None
                ),
                'total_quantity': brand['total_quantity'],
                'specifications': [
                    {
                        'spec_id': spec['order__specification'],
                        'spec_name': spec['order__specification__name'],
                        'total_quantity': spec['total_quantity']
                    }
                    for spec in specs
                ]
            })

        result = {
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "warehouse_location": warehouse.location,
            "brands": brand_list
        }

        return Response(result)


class StockTotalQuantityListView(APIView):

    def get(self, request):
        warehouse_id = request.query_params.get("warehouse_id")
        qs = Stock.objects.all()
        if warehouse_id:
            qs = qs.filter(warehouse=warehouse_id)
        total = qs.aggregate(total_quantity=Sum("stock_variants__quantity"))[
                    "total_quantity"] or 0

        return Response(total)





class StockAccessoryBrandListView(APIView):
    def get(self, request):
        warehouse_id = request.query_params.get("warehouse_id")
        if not warehouse_id:
            return Response({"detail": "warehouse_id is required"}, status=400)
        warehouse = Warehouse.objects.filter(id=warehouse_id).first()
        if not warehouse:
            return Response({"detail": "Warehouse not found"}, status=404)


        brands = (
            AccessoryStock.objects.filter(warehouse=warehouse).values(
                'accessory__brand',
                                          'accessory__brand__name',
                                          'accessory__brand__image')
            .annotate(total_quantity=Sum('total_quantity'))
            .order_by('accessory__brand__name')

        )
        brand_list = []
        for brand in brands:
            brand_id = brand['accessory__brand']
            name = (
                AccessoryStock.objects
                .filter(
                    accessory__brand__id=brand_id
                )
                .values('accessory__name',
                        )
                .annotate(total_quantity=Sum('total_quantity'))
                .order_by('accessory__name')
            )
            brand_list.append({
                'brand_id': brand_id,
                'brand_name': brand['accessory__brand__name'],
                'brand_image': request.build_absolute_uri(
                    f"/media/{brand['accessory__brand__image']}") if
                brand['accessory__brand__image'] else None,
                'total_quantity': brand['total_quantity'],
                'accessory_type': [
                    {
                        'name': name['accessory__name'],
                        'total_quantity': name['total_quantity']
                    }
                    for name in name
                ]
            })
        total_quantity=sum(c['total_quantity'] for c in brand_list)
        results={
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "warehouse_location": warehouse.name,
            "total_quantity":total_quantity,
            "brands": brand_list
        }
        return Response(results)


class StockAccessoryTypeListView(APIView):
    def get(self, request):
        warehouse_id = request.query_params.get("warehouse_id")
        if not warehouse_id:
            return Response({"detail": "warehouse_id is required"}, status=400)
        warehouse = Warehouse.objects.filter(id=warehouse_id).first()
        if not warehouse:
            return Response({"detail": "Warehouse not found"}, status=404)


        types_qs = (
            AccessoryStock.objects.filter(warehouse=warehouse).values(
                'accessory__name',
            )
            .annotate(total_quantity=Sum('total_quantity'))
            .order_by('accessory__name')
        )

        type_list = [
            {
                "type_name": t["accessory__name"],
                "total_quantity": t["total_quantity"]
            }
            for t in types_qs
        ]
        results={
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "warehouse_location": warehouse.location,
            "types": type_list
        }

        return Response(results)


class AccessoryStockExportPDFView(APIView):
    def get(self, request, *args, **kwargs):
        type_name = request.query_params.get('type_name')

        # Faqat type_name bo‘yicha filter
        queryset = AccessoryStock.objects.all()
        if type_name:
            queryset = queryset.filter(accessory__name__icontains=type_name)

        response = HttpResponse(content_type='application/pdf')
        response[
            'Content-Disposition'] = 'attachment; filename="accessory_stock.pdf"'

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        # Logo (agar kerak bo‘lsa)
        try:
            p.drawImage("media/logo.png", 50, height - 70, width=50, height=50)
        except:
            pass

        # Sarlavha
        p.setFont("Helvetica-Bold", 16)
        p.setFillColor(colors.darkblue)
        p.drawString(120, height - 50, "Accessory Stock Report")

        # Type info
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 90,
                     f"Type: {type_name if type_name else 'All'}")

        # Jadval ma'lumotlari
        data = [["№", "Brand", "Accessory Name", "Quantity"]]
        for idx, item in enumerate(queryset, start=1):
            data.append([
                idx,
                item.accessory.brand.name,
                item.accessory.name,
                f"{item.total_quantity:,}"
            ])

        # Table
        table = Table(data, colWidths=[2 * cm, 5 * cm, 8 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ]))

        table.wrapOn(p, width, height)
        table.drawOn(p, 50, height - 150)

        p.showPage()
        p.save()
        return response


class StockEntryViewSet(viewsets.ModelViewSet):
    queryset = StockEntry.objects.all()
    serializer_class = StockEntrySerializer

    def create(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            serializer = StockEntrySerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif "orders" in request.data:  # bulk kirim
            bulk_serializer = StockEntryBulkSerializer(data=request.data)
            bulk_serializer.is_valid(raise_exception=True)
            entries = bulk_serializer.save()
            return Response(
                StockEntrySerializer(entries, many=True).data,
                status=status.HTTP_201_CREATED
            )

        else:  # oddiy bitta yozuv
            serializer = StockEntrySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

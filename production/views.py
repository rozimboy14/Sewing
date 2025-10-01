import base64
from pathlib import Path

from django.contrib.staticfiles import finders
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q, F, Prefetch
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfgen import canvas
import io
import os
from reportlab.lib.units import mm

from rest_framework import viewsets, status, generics, request
from rest_framework.decorators import action

from rest_framework.response import Response
import openpyxl
from reportlab.graphics.barcode import code128
from weasyprint import HTML
from xhtml2pdf import pisa

from config import settings
from services.stock_service import create_production_report_with_daily, \
    NormCategoryService
from stock.models import Warehouse
from stock.signals import recalc_stock_quantity, \
    recalc_all_month_planing_orders
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .models import ProductionReport, LineOrders, Line, Daily, ProductionLine, \
    ProductionNorm, NormCategory, ProductionCategorySummary, MonthPlaningOrder, \
    MonthPlaning
from django.utils.timezone import now
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
font_path = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans.ttf')

pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
from .serializers import ProductionLineSerializer, ProductionReportSerializer, \
    LineOrdersSerializer, LineSerializer, DailySerializer, \
    ProductionNormSerializer, NormCategorySerializer, \
    ProductionNormBulkSerializer, ProductionCategorySummarySerializer, \
    MonthPlaningOrderSerializer, MonthPlaningSerializers


def generate_daily_entries(report_id, date=None):
    date = date or now().date()
    report = ProductionReport.objects.get(pk=report_id)
    line_orders = LineOrders.objects.filter(
        line_norm__production_report=report)

    for lo in line_orders:
        lo.create_daily(date=date)


class ProductionLineViewSet(viewsets.ModelViewSet):
    queryset = ProductionLine.objects.all()
    serializer_class = ProductionLineSerializer

    # filter_backends = [DjangoFilterBackend]
    # filterset_fields = {
    #     'warehouse_line__warehouse_id': ['exact'],
    # }

    def get_queryset(self):
        queryset = super().get_queryset()
        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            queryset = queryset.filter(
                warehouse_id=warehouse_id)
        return queryset



class ProductionReportViewSet(viewsets.ModelViewSet):
    queryset = ProductionReport.objects.all()
    serializer_class = ProductionReportSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        warehouse_id = self.request.query_params.get('warehouse_id')
        year = self.request.query_params.get('year')
        month = self.request.query_params.get('month')
        if warehouse_id:
            queryset = queryset.filter(
                warehouse_id=warehouse_id)
        if year:
            queryset = queryset.filter(
                year=year
            )
        if month:
            queryset = queryset.filter(
                month=month
            )

        return queryset

    def perform_create(self, serializer):
        data = serializer.validated_data
        warehouse = data['warehouse']
        year = data['year']
        month = data['month']
        comment = data.get('comment')

        # Service orqali yaratish
        report = create_production_report_with_daily(
            warehouse=warehouse,
            year=year,
            month=month,
            comment=comment
        )

        # serializer.instance ni set qilamiz, shunda response to‘g‘ri bo‘ladi
        serializer.instance = report


class LineViewSet(viewsets.ModelViewSet):
    queryset = Line.objects.all()



class LineOrdersViewSet(viewsets.ModelViewSet):
    queryset = LineOrders.objects.all()
    serializer_class = LineOrdersSerializer



class ProductionCategorySummaryViewSet(viewsets.ModelViewSet):
    queryset = ProductionCategorySummary.objects.all()
    serializer_class = ProductionCategorySummarySerializer


class DailyViewSet(viewsets.ModelViewSet):
    queryset = Daily.objects.all()
    serializer_class = DailySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['production_report']





class ProductionNormViewSet(viewsets.ModelViewSet):
    queryset = ProductionNorm.objects.all()
    serializer_class = ProductionNormSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['production_report']
    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create(self, request):
        serializer = ProductionNormBulkSerializer(data=request.data,
                                                  context={"request": request})
        serializer.is_valid(raise_exception=True)

        # bu yerda serializer.create chaqiriladi
        objs = serializer.save()

        return Response(
            ProductionNormSerializer(objs, many=True,
                                     context={"request": request}).data,
            status=status.HTTP_201_CREATED
        )
    def perform_create(self, serializer):
        data = serializer.validated_data
        production_report = data['production_report']
        line = data['line']

        # Service orqali yaratish
        production_norm  = NormCategoryService.create_norm_category(
            production_report=production_report,
            line=line,

        )

        # serializer.instance ni set qilamiz, shunda response to‘g‘ri bo‘ladi
        serializer.instance = production_norm




class NormCategoryViewSet(viewsets.ModelViewSet):
    queryset = NormCategory.objects.all()
    serializer_class = NormCategorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['production_norm__production_report']



class NormCategoryByReportView(generics.ListAPIView):
    serializer_class = NormCategorySerializer

    def get_queryset(self):
        report_id = self.kwargs['report_id']
        return NormCategory.objects.filter(
            production_norm__production_report_id=report_id
        ).select_related('order', 'order_variant', 'production_norm')

class MonthPlaningOrderViewSet(viewsets.ModelViewSet):
    queryset = MonthPlaningOrder.objects.all()
    serializer_class = MonthPlaningOrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['month_planing']

    def create(self, request, *args, **kwargs):
        is_many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def perform_create(self, serializer):
        serializer.save()


def link_callback(uri, rel):
    result = finders.find(uri)
    if result:
        path = result[0] if not isinstance(result, (list, tuple)) else result[
            0]
    else:
        path = os.path.join(settings.MEDIA_ROOT,
                            uri.replace(settings.MEDIA_URL, ""))
    if not os.path.isfile(path):
        raise Exception('Media URI must point to file: %s' % path)
    return path


class MonthPlaningViewSet(viewsets.ModelViewSet):
    queryset = MonthPlaning.objects.all()
    serializer_class = MonthPlaningSerializers

    def get_queryset(self):
        queryset = super().get_queryset()
        warehouse_id = self.request.query_params.get('warehouse_id')
        year = self.request.query_params.get('year')
        month = self.request.query_params.get('month')
        if warehouse_id:
            queryset = queryset.filter(
                warehouse_id=warehouse_id)
        if year:
            queryset = queryset.filter(
                year=year
            )
        if month:
            queryset = queryset.filter(
                month=month
            )

        return queryset

    from xhtml2pdf import pisa

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        planning = self.get_object()
        template = get_template("production/month_planing.html")
        html_string = template.render({
            "planning": planning,
            "MEDIA_URL": settings.MEDIA_URL,  # Media fayllar uchun
            "STATIC_URL": settings.STATIC_URL,  # Static fayllar uchun
        })

        # PDF yaratish
        pdf_file = HTML(
            string=html_string,
            base_url=request.build_absolute_uri('/')
            # Media va static fayllarni topish uchun
        ).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response[
            'Content-Disposition'] = 'attachment; filename="month_planing.pdf"'
        return response


@api_view(["POST"])
def refresh_stock_quantity(request, order_id):
    updated_quantity = recalc_stock_quantity(order_id)
    return Response({"stock_quantity": updated_quantity})


@api_view(['POST'])
def refresh_all_month_planing_orders(request):
    updated = recalc_all_month_planing_orders()
    return Response({"status": "ok", "updated": updated})


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_excel(request):
    excel_file = request.FILES.get("file")
    if not excel_file:
        return Response({"error": "Fayl yuborilmadi"}, status=400)

    wb = openpyxl.load_workbook(excel_file)
    sheet = wb.active

    page_width = 115 * mm
    page_height = 50 * mm

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True),
                              start=1):
        code = str(row[0])
        if code and code != "None":
            barcode_obj = code128.Code128(
                code,
                barHeight=35 * mm,
                barWidth=0.80 * mm,
                humanReadable=False
            )
            x = (page_width - barcode_obj.width) / 2
            y = 9 * mm
            barcode_obj.drawOn(c, x, y)

            font_size = 22
            char_space = 3.1
            text_obj = c.beginText()
            text_obj.setFont("Helvetica-Bold", font_size)
            text_obj.setCharSpace(char_space)

            text_width = c.stringWidth(code, "Helvetica-Bold",
                                       font_size) + char_space * (
                                     len(code) - 1)
            x_text = (page_width - text_width) / 2
            y_text = y - 18
            text_obj.setTextOrigin(x_text, y_text)
            text_obj.textLine(code)
            c.drawText(text_obj)
            # Tepaga tartib raqamini yozish (№:1, №:2 ...)

            c.setFont("DejaVuSans", 10)
            c.drawString(10, page_height - 12, f"№:{idx}   Синий")

            c.showPage()

    c.save()
    pdf_value = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_value, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="barcodes.pdf"'
    return response

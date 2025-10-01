from django.db.models import Sum

from production.models import ProductionCategorySummary, LineOrders, \
    NormCategory


def update_category_summaries(production_report):
    # Oldingi natijalarni tozalaymiz
    ProductionCategorySummary.objects.filter(production_report=production_report).delete()

    # 1. Normalarni yig‘ish
    norm_data = (
        NormCategory.objects.filter(production_norm__production_report=production_report)
        .values('category')
        .annotate(total_norm=Sum('norm'))
    )

    # 2. Fakt chiqqan miqdorlarni yig‘ish
    actual_data = (
        LineOrders.objects.filter(order_line__line_daily__production_report=production_report)
        .values('order__category')
        .annotate(total_quantity=Sum('quantity'))
    )

    # Convert to dict for quick access
    actual_map = {item['order__category']: item['total_quantity'] for item in actual_data}

    # 3. Natijalarni yaratish
    for norm_item in norm_data:
        category_id = norm_item['category']
        norm = norm_item['total_norm']
        actual = actual_map.get(category_id, 0)

        ProductionCategorySummary.objects.create(
            production_report=production_report,
            category_id=category_id,
            norm=norm,
            actual=actual
        )

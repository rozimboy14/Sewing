from django.contrib import admin
from .models import (
    Brand,
    Specification,
    SewingCategory,
    PackagingCategory,
    Article,
    Order, Accessory, ArticleAccessory
)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name__name',)  # ForeignKey bo‘lgani uchun

@admin.register(SewingCategory)
class SewingCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'norm')
    search_fields = ('name',)

@admin.register(PackagingCategory)
class PackagingCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'norm')
    search_fields = ('name',)


class ArticleAccessoryInline(admin.TabularInline):
    model = ArticleAccessory
    extra = 1


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'article', 'brand', 'sewing_category',
                    'packaging_category','get_accessories')
    search_fields = ('name', 'article')
    list_filter = ('brand', 'sewing_category', 'packaging_category')
    inlines = [ArticleAccessoryInline]

    def get_accessories(self, obj):
        return ", ".join([a.name for a in obj.accessories.all()])
    get_accessories.short_description = "Accessories"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'specification', 'article', 'quantity')
    list_filter = ('specification__name', 'article')

@admin.register(Accessory)
class AccessoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'brand')






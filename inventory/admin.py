from django.contrib import admin
from .models import Item
from .models import StockIn
from django.utils.safestring import mark_safe


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'weighted_avg_cost', 'critical_point', 'image_preview')  # 新增 image_preview
    search_fields = ('name',)
    readonly_fields = ('image_preview',)  # 預覽圖片用

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 50px;" />')
        return "No Image"
    image_preview.short_description = 'Image Preview'  # 欄位顯示名稱


@admin.register(StockIn)
class StockInAdmin(admin.ModelAdmin):
    list_display = ('unitcost', 'quantity','last_vendor')

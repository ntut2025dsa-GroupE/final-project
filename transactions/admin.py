from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('item', 'unitprice', 'quantity', 'timestamp', 'demander')
    search_fields = ('item__name', 'demander')
    list_filter = ('timestamp', 'demander')

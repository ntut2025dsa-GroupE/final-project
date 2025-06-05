from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from .models import Transaction
from inventory.models import Item, StockIn
from datetime import date
from django.forms.widgets import Select
from django.utils.html import format_html
from django.db.models import Sum, Case, When, IntegerField, Q
from django.utils.timezone import now


class CustomSelect(Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        
        print(option)
        
        if hasattr(self, 'wac_data') and value in self.wac_data:
            option['attrs']['data-wac'] = self.wac_data[value]
            
        if hasattr(self, 'tq_data') and value in self.tq_data:
            option['attrs']['data-tq'] = self.tq_data[value]
            
        return option

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['item', 'unitprice', 'quantity', 'demander', 'notes']
        widgets = {
            'item': CustomSelect()  # 使用自定義小部件
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unitprice'].validators.append(MinValueValidator(0.01))
        today = now().date()
        
        items = Item.objects.annotate(
        total_quantity=Sum(
                Case(
                    When(stockins__expiry_date__gte=today, then='stockins__quantity'),
                    When(stockins__expiry_date__isnull=True, then='stockins__quantity'),
                    default=0,
                    output_field=IntegerField()
                )
            )
        ).distinct()
        
        # 過濾唯一商品
        unique_items = {}
        wac_data = {}
        tq_data = {}
        for item in items:
            if item.name not in unique_items:
                unique_items[item.name] = item.id
                wac_data[item.id] = f"{item.weighted_avg_cost:.2f}"
                tq_data[item.id] = f"{item.total_quantity or 0}"
        
        self.fields['item'].queryset = Item.objects.filter(id__in=unique_items.values())
        self.fields['item'].widget.wac_data = wac_data  # 傳遞成本數據
        self.fields['item'].widget.tq_data = tq_data  # 傳遞總量數據

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('item')
        quantity = cleaned_data.get('quantity')

        if item and quantity:
            stock_ins = StockIn.objects.filter(
                item=item,
                expiry_date__gte=date.today(),  # 改成用 date.today()
                quantity__gt=0
            )
            total_available = sum(stock.quantity for stock in stock_ins)

            if quantity > total_available:
                # 使用 span 包裹錯誤訊息，避免自動添加項目符號
                error_msg = format_html(
                    '<span style="display:inline-block">⚠️ Insufficient / Expired ! now we have only {} {}</span>',
                    total_available,
                    item.name
                )
                self.add_error('quantity', error_msg)

        return cleaned_data
    
class ExportForm(forms.Form):
    DATE_RANGE_CHOICES = [
        ('all', 'All Data'),
        ('day', 'Specific Day'),
        ('month', 'Specific Month'),
        ('year', 'Specific Year'),
    ]
    
    date_range = forms.ChoiceField(
        choices=DATE_RANGE_CHOICES,
        initial='all',
        widget=forms.RadioSelect
    )
    
    custom_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Select Date"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_range = cleaned_data.get('date_range')
        custom_date = cleaned_data.get('custom_date')
        
        if date_range != 'all' and not custom_date:
            raise ValidationError("Please select a date for the chosen range.")
        
        return cleaned_data

from django import forms
from .models import Item
from .models import StockIn

class ItemForm(forms.ModelForm):
    # 明確定義 image 欄位並啟用清除功能
    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control-file'
        })
    )
    
    class Meta:
        model = Item
        fields = ['name', 'image', 'category', 'critical_point', 'lead_time_demand']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lead_time_demand'].widget = forms.NumberInput(attrs={'step': '0.1'})
        
        # 為 image 欄位設定更好的標籤和幫助文字
        self.fields['image'].label = 'Product Image'
        self.fields['image'].help_text = 'Upload an image for this item. Check "Clear" to remove existing image.'
        print(self.fields)
    def clean_lead_time_demand(self):
        lead_time_demand = self.cleaned_data['lead_time_demand']
        if not (0.1 <= lead_time_demand <= 1.0):
            raise forms.ValidationError("lead_time_demand must between 0.1 and 1.0")
        return lead_time_demand

class StockInRecords(forms.ModelForm):
    expiry_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format='%Y/%m/%d',
            attrs={'type': 'date'}
        )
    )
    class Meta:
        model = StockIn
        fields = ['unitcost', 'quantity', 'last_vendor', 'created_at', 'expiry_date']
        widgets = {
            'created_at': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

class StockInForm(forms.ModelForm):
    class Meta:
        model = StockIn
        fields = ['unitcost', 'quantity', 'last_vendor', 'created_at', 'expiry_date']
        widgets = {
            'created_at': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
from django.shortcuts import render, redirect
from inventory.models import Item  # 假設您的 Item 模型在 inventory 應用中
from django.db.models import Sum, Case, When, IntegerField, Q
from django.utils.timezone import now






def home_page(request):
    today = now().date()
    items = Item.objects.annotate(
        quantity=Sum(
            Case(
                When(stockins__expiry_date__gte=today, then='stockins__quantity'),
                When(stockins__expiry_date__isnull=True, then='stockins__quantity'),
                default=0,
                output_field=IntegerField()
            )
        )
    ).distinct()
    
    return render(request, 'homepage/homepage.html', {'items': items})



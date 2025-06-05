from django.shortcuts import render, redirect, get_object_or_404
from .models import Item, StockIn
from .forms import ItemForm
from .forms import StockInForm
from .forms import StockInRecords
from django.db.models import Sum, Case, When, IntegerField, Q
from datetime import date
from django.utils.timezone import now
from django.db import models
from django.db.models import F
from math import ceil



def item_list(request):
    sort = request.GET.get('sort', 'name')  # 預設排序為 name
    query = request.GET.get('query', '')
    today = now().date()

    # 有效庫存總量
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
    
    if query:
        items = items.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query) |
            Q(total_quantity__icontains=query) |
            Q(critical_point__icontains=query) 
        ).distinct()
    
    for item in items:
        reorder_point = ceil(item.critical_point * (1 + item.lead_time_demand))
        current_quantity = item.total_quantity or 0
        
        if current_quantity <= reorder_point:
            item.level = 'reorder'
            if current_quantity <= item.critical_point:
                item.level = 'critical'
        else:
            item.level = 'normal'
            
        item.reorder_point = reorder_point
    
            
    # 轉 list 以利使用 Python 屬性排序（weighted_avg_cost 是 Python 屬性）
    items = list(items)

    # 排序邏輯（支援 weighted_avg_cost 與 total_quantity 以外的 model 欄位）
    reverse = sort.startswith('-')
    sort_key = sort.lstrip('-')

    if sort_key == 'reorder_point':
        items.sort(key=lambda i: i.reorder_point, reverse=reverse)
    if sort_key == 'weighted_avg_cost':
        items.sort(key=lambda i: i.weighted_avg_cost if i.weighted_avg_cost is not None else 0, reverse=reverse)
    elif sort_key == 'total_quantity':
        items.sort(key=lambda i: i.total_quantity if i.total_quantity is not None else 0, reverse=reverse)
    else:
        # 驗證是否為 Item 的合法欄位，避免用戶輸入非法欄位導致錯誤
        valid_fields = [f.name for f in Item._meta.fields]
        if sort_key in valid_fields:
            items.sort(key=lambda i: getattr(i, sort_key) or '', reverse=reverse)

    
    return render(request, 'inventory/item_list.html', {
        'items': items,
        'current_sort': sort,
        'query': query,
    })



def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    sort = request.GET.get('sort', 'created_at')  # 預設排序欄位
    query = request.GET.get('query', '')

    stockins = StockIn.objects.filter(item=item)

    if query:
        stockins = stockins.filter(
            Q(serial_number__icontains=query) |
            Q(last_vendor__icontains=query)
        )

    # 避免排序欄位輸入非法值造成錯誤
    allowed_sort_fields = ['serial_number', 'created_at', 'unitcost', 'quantity', 'last_vendor', 'expiry_date']
    sort_field = sort.lstrip('-')
    if sort_field in allowed_sort_fields:
        stockins = stockins.order_by(sort)

    context = {
        'item': item,
        'stockins': stockins,
        'sort': sort,
        'query': query,
        'today': now().date(),
    }
    return render(request, 'inventory/item_detail.html', context)

def item_create(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.save()  # 保存新項目
            return redirect('inventory:item_list')
    else:
        form = ItemForm()
        
    return render(request, 'inventory/add_item.html', {'form': form})


def Stock_In_Records(request):  # 買入紀錄
    sort = request.GET.get('sort', 'timestamp')  # 預設按時間排序
    query = request.GET.get('query', '')
    item_id = request.GET.get('item_id')
    item = get_object_or_404(Item, pk=item_id)

    if request.method == 'POST':
        form = StockInRecords(request.POST)
        if form.is_valid():
            stockin = form.save(commit=False)
            stockin.item = item
            stockin.save()
            return redirect('inventory:item_detail', item_id=item_id)
    else:
        form = StockInRecords()

    # 查詢並排序該 item 的 stockin 記錄
    stockins = item.stockins.all()

    if query:
        stockins = stockins.filter(notes__icontains=query)

    if sort in ['quantity', 'unitcost', 'created_at']:
        stockins = stockins.order_by(sort)
    elif sort.startswith('-') and sort[1:] in ['quantity', 'unitcost', 'created_at']:
        stockins = stockins.order_by(sort)
    
    return render(request, 'inventory/add_stockin.html', {
        'form': form,
        'item': item,
        'stockins': stockins,
        'sort': sort,
        'query': query
    })

def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('inventory:item_list')
    else:
        form = ItemForm(instance=item)
    return render(request, 'inventory/item_update.html', {'form': form})

def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('inventory:item_list')
    return render(request, 'inventory/item_confirm_delete.html', {'item': item})

def stockin_update(request, pk):
    stockin = get_object_or_404(StockIn, pk=pk)
    if request.method == 'POST':
        form = StockInForm(request.POST, instance=stockin)
        if form.is_valid():
            form.save()
            return redirect('inventory:item_detail', item_id=stockin.item.pk)
    else:
        form = StockInForm(instance=stockin)
    return render(request, 'inventory/stockin_update.html', {'form': form})

def stockin_delete(request, pk):
    stockin = get_object_or_404(StockIn, pk=pk)
    if request.method == 'POST':
        item_pk = stockin.item.pk
        stockin.delete()
        return redirect('inventory:item_detail', item_id=item_pk)
    return render(request, 'inventory/stockin_confirm_delete.html', {'stockin': stockin})

def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)  
        if form.is_valid():
            form.save()
            return redirect('homepage/homepage.html') 
    else:
        form = ItemForm()
    return render(request, 'homepage/homepage.html', {'form': form})

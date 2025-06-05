from django.shortcuts import render, redirect 
from .models import Transaction
from .forms import TransactionForm, ExportForm
from inventory.models import StockIn
from django.db import transaction as db_transaction  # 為了資料一致性
from django.utils import timezone  # 加入這行以取得當下時間
from django.db.models import Q
import csv
from django.http import HttpResponse
from dateutil.relativedelta import relativedelta
from dateutil import parser
import re
from datetime import date


def transaction_list(request):
    query = request.GET.get('query', '').strip()
    sort = request.GET.get('sort', '-timestamp')
    transactions = Transaction.objects.select_related('item')  # 優化查詢
    
    if query:
        date_filtered = False
        
        # 日期格式模式
        year_pattern = r'^\d{4}$'
        year_month_pattern = r'^\d{4}[-/]\d{1,2}$'
        full_date_pattern = r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$'
        
        try:
            if re.match(year_pattern, query):
                year = int(query)
                start_date = date(year, 1, 1)
                end_date = date(year + 1, 1, 1)
                date_filtered = True
                
            elif re.match(year_month_pattern, query):
                parsed_date = parser.parse(query, dayfirst=False)
                start_date = parsed_date.date().replace(day=1)
                end_date = start_date + relativedelta(months=1)
                date_filtered = True
                
            elif re.match(full_date_pattern, query):
                parsed_date = parser.parse(query, dayfirst=False)
                start_date = parsed_date.date()
                end_date = start_date + relativedelta(days=1)
                date_filtered = True
            
            if date_filtered:
                transactions = transactions.filter(
                    timestamp__date__gte=start_date,
                    timestamp__date__lt=end_date
                )
                
        except (ValueError, OverflowError, TypeError):
            date_filtered = False
        
        # 文字搜尋
        if not date_filtered or not transactions.exists():
            if date_filtered and not transactions.exists():
                transactions = Transaction.objects.select_related('item')
            
            search_conditions = Q(
                notes__icontains=query
            ) | Q(
                demander__icontains=query 
            ) | Q(
                item__name__icontains=query
            )
            
            # 如果查詢是數字，也搜尋金額和數量
            if query.replace('.', '').replace('-', '').isdigit():
                try:
                    number = float(query)
                    search_conditions |= Q(unitprice=number) | Q(quantity=int(number))
                except (ValueError, OverflowError):
                    pass
            
            transactions = transactions.filter(search_conditions)
    
    # 確保排序欄位有效
    valid_sorts = ['-timestamp', 'timestamp', '-unitprice', 'unitprice', 
                   'demander', '-demander', 'quantity', '-quantity']
    if sort not in valid_sorts:
        sort = '-timestamp'
    
    transactions = transactions.order_by(sort)
    
    return render(request, 'transactions/transaction_list.html', {
        'transactions': transactions,
        'query': query,
        'sort': sort,
    })

def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            with db_transaction.atomic():
                transaction_obj = form.save(commit=False)
                item = transaction_obj.item
                required_quantity = transaction_obj.quantity

                # ✅ 表單已保證庫存足夠，因此這裡只要扣庫存
                stockins = StockIn.objects.filter(
                    item=item,
                    expiry_date__gte=timezone.now().date()
                ).order_by('expiry_date', 'created_at')

                for stockin in stockins:
                    if required_quantity <= 0:
                        break

                    available = stockin.quantity
                    used_quantity = min(available, required_quantity)

                    stockin.quantity -= used_quantity
                    required_quantity -= used_quantity

                    if stockin.quantity <= 0:
                        stockin.delete()
                    else:
                        stockin.save()

                transaction_obj.save()
                return redirect('transactions:transaction_list')
        else:
            print("❌ 表單驗證失敗", form.errors)
    else:
        form = TransactionForm()

    return render(request, 'transactions/add_transaction.html', {'form': form})

def export_csv(request):
    if request.method == 'POST':
        form = ExportForm(request.POST)
        if form.is_valid():
            date_range = form.cleaned_data['date_range']
            custom_date = form.cleaned_data['custom_date']
            
            transactions = Transaction.objects.all()
            
            if date_range == 'day' and custom_date:
                transactions = transactions.filter(timestamp__date=custom_date)
            elif date_range == 'month' and custom_date:
                start_date = custom_date.replace(day=1)
                end_date = start_date + relativedelta(months=1)
                transactions = transactions.filter(timestamp__date__gte=start_date, timestamp__date__lt=end_date)
            elif date_range == 'year' and custom_date:
                start_date = custom_date.replace(month=1, day=1)
                end_date = start_date + relativedelta(years=1)
                transactions = transactions.filter(timestamp__date__gte=start_date, timestamp__date__lt=end_date)
            
            # 排序
            sort = request.GET.get('sort', 'timestamp')
            if sort in ['timestamp', 'item__name', 'unitprice', 'quantity', 'demander', 'notes']:
                transactions = transactions.order_by(sort)
            elif sort.startswith('-') and sort[1:] in ['timestamp', 'item__name', 'unitprice', 'quantity', 'demander', 'notes']:
                transactions = transactions.order_by(sort)

            # 輸出 CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

            writer = csv.writer(response)
            writer.writerow(['Item', 'Unit Price', 'Quantity', 'Timestamp', 'Demander', 'Notes'])

            for t in transactions:
                writer.writerow([
                    t.item.name,
                    t.unitprice,
                    t.quantity,
                    t.timestamp.strftime('%Y-%m-%d %H:%M'),
                    t.demander,
                    t.notes
                ])

            return response
    else:
        form = ExportForm()

    return render(request, 'transactions/export_modal.html', {'form': form})
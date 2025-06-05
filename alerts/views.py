from django.shortcuts import render
from inventory.models import Item, StockIn
from datetime import date
from math import ceil

def alert_view(request):
    today = date.today()
    alerts = []

    # 所有品項
    items = Item.objects.all()

    for item in items:
        # 計算目前有效庫存（過期的不算）
        valid_stockins = item.stockins.filter(expiry_date__gte=today) | item.stockins.filter(expiry_date__isnull=True)
        current_quantity = sum(stock.quantity for stock in valid_stockins)
        
        reorder_point = ceil(item.critical_point * (1 + item.lead_time_demand))
        if current_quantity <= reorder_point:
            level = 'reorder'
            if current_quantity <= item.critical_point:
                level = 'critical'
        else:
            level = 'normal'

        alerts.append({
            'name': item.name,
            'total_quantity': current_quantity,
            'reorder_point': reorder_point,
            'critical_point': item.critical_point,
            'alert_level': level,
        })

    # 找出過期的庫存
    expired_stockins = StockIn.objects.filter(expiry_date__lt=today)
     

    return render(request, 'alerts/alert_list.html', {
        'alerts': alerts,
        'expired_stockins': expired_stockins
    })

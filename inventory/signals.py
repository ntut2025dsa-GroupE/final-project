from django.db.models.signals import pre_save 
from django.dispatch import receiver
from .models import StockIn
import re

@receiver(pre_save, sender=StockIn)
def set_serial_number(sender, instance, **kwargs):
    if not instance.serial_number and instance.item:
        last_stockin = (
            StockIn.objects
            .filter(item=instance.item)
            .exclude(serial_number=None)
            .order_by('-id')  # 這樣避免字串排序問題
            .first()
        )
        if last_stockin and last_stockin.serial_number:
            match = re.search(r'\d+', last_stockin.serial_number)
            if match:
                last_number = int(match.group())
                instance.serial_number = f"S{last_number + 1:03d}"
            else:
                instance.serial_number = "S001"
        else:
            instance.serial_number = "S001"

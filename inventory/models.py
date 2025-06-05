from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.db.models import F
from decimal import Decimal



class Item(models.Model):
    CATEGORY_CHOICES = [('food','food'),]  
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    critical_point = models.IntegerField(default=0) 
    lead_time_demand = models.FloatField(
        validators=[MinValueValidator(0.1), MaxValueValidator(1.0)],
        help_text="please enter a number between 0.1 ~ 1.0 as the system criteria",
        default=0.1
    )
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)

    def __str__(self):
        return self.name
    
    @property
    def weighted_avg_cost(self):
        today = now().date()
        
        aggregate = self.stockins.filter(
            models.Q(expiry_date__gte=today) | models.Q(expiry_date__isnull=True)
        ).aggregate(
            total_cost=models.Sum(models.F('unitcost') * models.F('quantity')),
            total_quantity=models.Sum('quantity')
        )
        
        total_cost = aggregate['total_cost'] or Decimal('0')
        total_quantity = aggregate['total_quantity'] or Decimal('0')
        
        if total_quantity > 0:
            return (total_cost / total_quantity).quantize(Decimal('0.00'))
        return Decimal('0.00')
            

class StockIn(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='stockins')
    serial_number = models.CharField(max_length=10)
    unitcost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0.00)
    quantity = models.IntegerField(default=0)
    last_vendor = models.CharField(max_length=25, null=True, blank=True)
    created_at = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('item', 'serial_number') 
    

    def __str__(self):
        return f"{self.item.name} - {self.quantity} units @ {self.created_at}"

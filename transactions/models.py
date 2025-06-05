from django.db import models
from inventory.models import Item
from django.core.validators import MinValueValidator
from decimal import Decimal



class Transaction(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='transactions')
    unitprice = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),  # 使用 Decimal 而不是 0
        validators=[MinValueValidator(Decimal('0.00'))]  # 確保價格不為負
    )
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    timestamp = models.DateTimeField(auto_now_add=True)
    demander = models.CharField(  # 改為小寫，符合 Python 慣例
        max_length=50,
        default='Unknown',
        db_index=True  # 為常用搜尋欄位加索引
    )
    notes = models.TextField(blank=True, null=True)  # 加入 null=True

    class Meta:
            # 加入資料庫索引提升搜尋效能
            indexes = [
                models.Index(fields=['timestamp']),
                models.Index(fields=['demander']),
                models.Index(fields=['timestamp', 'demander']),  # 複合索引
                models.Index(fields=['-timestamp']),  # 用於預設排序
            ]
            
            # 預設排序
            ordering = ['-timestamp']
            
            # 友好的複數名稱
            verbose_name = 'Transaction'
            verbose_name_plural = 'Transactions'
        
    def  __str__(self):
       return f"{self.item.name} - {self.quantity} pcs on {self.timestamp.strftime('%Y-%m-%d')}"
   
    def formatted_timestamp(self):
        """格式化時間戳的方法"""
        return self.timestamp.strftime('%Y-%m-%d %H:%M')
    
    def __repr__(self):
        return f"Transaction(id={self.id}, item='{self.item.name}', quantity={self.quantity})"




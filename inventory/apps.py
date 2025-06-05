from django.apps import AppConfig

class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory"

    def ready(self):
        import inventory.signals  # ✅ 僅保留這行來載入 signals.py


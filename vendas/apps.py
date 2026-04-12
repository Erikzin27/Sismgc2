from django.apps import AppConfig


class VendasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "vendas"
    verbose_name = "Vendas"
    
    def ready(self):
        """Registra signals quando a app é carregada."""
        import vendas.signals  # noqa: F401

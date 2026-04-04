from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
handler403 = "sismgc.views.permission_denied_view"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("core.urls")),
    path("", include("dashboard.urls")),
    path("usuarios/", include("usuarios.urls")),
    path("linhagens/", include("linhagens.urls")),
    path("aves/", include("aves.urls")),
    path("lotes/", include("lotes.urls")),
    path("genetica/", include("genetica.urls")),
    path("incubacao/", include("incubacao.urls")),
    path("nascimentos/", include("nascimentos.urls")),
    path("estoque/", include("estoque.urls")),
    path("alimentacao/", include("alimentacao.urls")),
    path("sanidade/", include("sanidade.urls")),
    path("abate/", include("abate.urls")),
    path("vendas/", include("vendas.urls")),
    path("financeiro/", include("financeiro.urls")),
    path("relatorios/", include("relatorios.urls")),
    path("historico/", include("historico.urls")),
    path("calendario/", include("calendario.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

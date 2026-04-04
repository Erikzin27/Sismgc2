from django.urls import path
from .views import (
    GlobalSearchView,
    ConfiguracaoView,
    AdminAreaView,
    AdminSegurancaView,
    AdminBackupView,
    AdminIdentidadeView,
    AdminBackupDBView,
    AdminBackupMediaView,
    AdminParametrosView,
)

app_name = "core"

urlpatterns = [
    path("search/", GlobalSearchView.as_view(), name="search"),
    path("configuracoes/", ConfiguracaoView.as_view(), name="configuracoes"),
    path("admin-area/", AdminAreaView.as_view(), name="admin_area"),
    path("admin-area/seguranca/", AdminSegurancaView.as_view(), name="admin_seguranca"),
    path("admin-area/backup/", AdminBackupView.as_view(), name="admin_backup"),
    path("admin-area/identidade/", AdminIdentidadeView.as_view(), name="admin_identidade"),
    path("admin-area/parametros/", AdminParametrosView.as_view(), name="admin_parametros"),
    path("admin-area/backup/db/", AdminBackupDBView.as_view(), name="admin_backup_db"),
    path("admin-area/backup/media/", AdminBackupMediaView.as_view(), name="admin_backup_media"),
]

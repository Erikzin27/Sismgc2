from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.UserListView.as_view(), name="list"),
    path("novo/", views.UserCreateView.as_view(), name="create"),
    path("<int:pk>/", views.UserDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.UserUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.UserDeleteView.as_view(), name="delete"),
    path("<int:pk>/toggle-ativo/", views.UserToggleActiveView.as_view(), name="toggle_active"),
    path("export/excel/", views.UserExportExcelView.as_view(), name="export_excel"),
    path("export/pdf/", views.UserExportPDFView.as_view(), name="export_pdf"),
    path("perfil/meu/", views.ProfileView.as_view(), name="profile"),
]

from django.urls import path
from . import views

app_name = "reprodutores"

urlpatterns = [
    # Dashboard
    path("", views.DashboardReprodutivyView.as_view(), name="dashboard"),
    
    # Reprodutores
    path("reprodutores/", views.ReprodutorListView.as_view(), name="list"),
    path("reprodutores/novo/", views.ReprodutorCreateView.as_view(), name="create"),
    path("reprodutores/<int:pk>/", views.ReprodutorDetailView.as_view(), name="detail"),
    path("reprodutores/<int:pk>/editar/", views.ReprodutorUpdateView.as_view(), name="update"),
    path("reprodutores/<int:pk>/excluir/", views.ReprodutorDeleteView.as_view(), name="delete"),
    
    # Casais
    path("casais/", views.CasalListView.as_view(), name="casal_list"),
    path("casais/novo/", views.CasalCreateView.as_view(), name="casal_create"),
    path("casais/<int:pk>/", views.CasalDetailView.as_view(), name="casal_detail"),
    path("casais/<int:pk>/editar/", views.CasalUpdateView.as_view(), name="casal_update"),
    path("casais/<int:pk>/excluir/", views.CasalDeleteView.as_view(), name="casal_delete"),
]

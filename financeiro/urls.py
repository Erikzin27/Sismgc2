from django.urls import path
from . import views

app_name = "financeiro"

urlpatterns = [
    path("dashboard/", views.FinanceiroDashboardView.as_view(), name="dashboard"),
    path("orcamentos/", views.OrcamentoFuturoListView.as_view(), name="orcamento_list"),
    path("orcamentos/novo/", views.OrcamentoFuturoCreateView.as_view(), name="orcamento_create"),
    path("orcamentos/<int:pk>/", views.OrcamentoFuturoDetailView.as_view(), name="orcamento_detail"),
    path("orcamentos/<int:pk>/editar/", views.OrcamentoFuturoUpdateView.as_view(), name="orcamento_update"),
    path("orcamentos/<int:pk>/excluir/", views.OrcamentoFuturoDeleteView.as_view(), name="orcamento_delete"),
    path("", views.LancamentoListView.as_view(), name="list"),
    path("novo/", views.LancamentoCreateView.as_view(), name="create"),
    path("<int:pk>/", views.LancamentoDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.LancamentoUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.LancamentoDeleteView.as_view(), name="delete"),
]

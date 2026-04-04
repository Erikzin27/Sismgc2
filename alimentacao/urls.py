from django.urls import path
from . import views

app_name = "alimentacao"

urlpatterns = [
    path("", views.FormulaListView.as_view(), name="list"),
    path("nova/", views.FormulaCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", views.FormulaUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.FormulaDeleteView.as_view(), name="delete"),
]

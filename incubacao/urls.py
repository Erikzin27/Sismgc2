from django.urls import path
from . import views

app_name = "incubacao"

urlpatterns = [
    path("", views.IncubacaoListView.as_view(), name="list"),
    path("nova/", views.IncubacaoCreateView.as_view(), name="create"),
    path("<int:pk>/", views.IncubacaoDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.IncubacaoUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.IncubacaoDeleteView.as_view(), name="delete"),
]

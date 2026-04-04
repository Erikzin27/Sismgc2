from django.urls import path
from . import views

app_name = "aves"

urlpatterns = [
    path("", views.AveListView.as_view(), name="list"),
    path("nova/", views.AveCreateView.as_view(), name="create"),
    path("<int:pk>/", views.AveDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.AveUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.AveDeleteView.as_view(), name="delete"),
]

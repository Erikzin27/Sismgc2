from django.urls import path
from . import views

app_name = "linhagens"

urlpatterns = [
    path("", views.LinhagemListView.as_view(), name="list"),
    path("nova/", views.LinhagemCreateView.as_view(), name="create"),
    path("<int:pk>/", views.LinhagemDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.LinhagemUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.LinhagemDeleteView.as_view(), name="delete"),
]

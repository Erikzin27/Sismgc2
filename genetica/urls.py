from django.urls import path
from . import views

app_name = "genetica"

urlpatterns = [
    path("", views.RegistroListView.as_view(), name="list"),
    path("novo/", views.RegistroCreateView.as_view(), name="create"),
    path("<int:pk>/", views.RegistroDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.RegistroUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.RegistroDeleteView.as_view(), name="delete"),
]

from django.urls import path
from . import views

app_name = "abate"

urlpatterns = [
    path("", views.AbateListView.as_view(), name="list"),
    path("novo/", views.AbateCreateView.as_view(), name="create"),
    path("<int:pk>/", views.AbateDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.AbateUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.AbateDeleteView.as_view(), name="delete"),
]

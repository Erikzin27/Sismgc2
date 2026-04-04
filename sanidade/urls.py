from django.urls import path
from . import views

app_name = "sanidade"

urlpatterns = [
    path("vacinas/", views.VacinaListView.as_view(), name="vacina_list"),
    path("vacinas/<int:pk>/", views.VacinaDetailView.as_view(), name="vacina_detail"),
    path("vacinas/nova/", views.VacinaCreateView.as_view(), name="vacina_create"),
    path("vacinas/<int:pk>/editar/", views.VacinaUpdateView.as_view(), name="vacina_update"),
    path("vacinas/<int:pk>/excluir/", views.VacinaDeleteView.as_view(), name="vacina_delete"),
    path("medicamentos/", views.MedicamentoListView.as_view(), name="medicamento_list"),       
    path("medicamentos/<int:pk>/", views.MedicamentoDetailView.as_view(), name="medicamento_detail"),
    path("medicamentos/novo/", views.MedicamentoCreateView.as_view(), name="medicamento_create"),
    path("medicamentos/<int:pk>/editar/", views.MedicamentoUpdateView.as_view(), name="medicamento_update"),
    path("medicamentos/<int:pk>/excluir/", views.MedicamentoDeleteView.as_view(), name="medicamento_delete"),
    path("aplicacoes/", views.AplicacaoListView.as_view(), name="aplicacao_list"),
    path("aplicacoes/nova/", views.AplicacaoCreateView.as_view(), name="aplicacao_create"),
    path("aplicacoes/<int:pk>/editar/", views.AplicacaoUpdateView.as_view(), name="aplicacao_update"),
    path("aplicacoes/<int:pk>/excluir/", views.AplicacaoDeleteView.as_view(), name="aplicacao_delete"),
    path("tratamentos/", views.TratamentoListView.as_view(), name="tratamento_list"),
    path("tratamentos/novo/", views.TratamentoCreateView.as_view(), name="tratamento_create"),
    path("tratamentos/<int:pk>/editar/", views.TratamentoUpdateView.as_view(), name="tratamento_update"),
    path("tratamentos/<int:pk>/excluir/", views.TratamentoDeleteView.as_view(), name="tratamento_delete"),
    path("vacinas/lote/<int:pk>/", views.VacinaLoteListView.as_view(), name="vacina_lote"),
    path("vacinas/lote/<int:pk>/ok/<int:vacina_id>/", views.VacinaLoteMarcarView.as_view(), name="vacina_lote_ok"),
]

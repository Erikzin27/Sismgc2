from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin
from .models import Vacina, Medicamento, AplicacaoVacina, Tratamento, VacinaLote
from .forms import (
    VacinaForm,
    MedicamentoForm,
    AplicacaoVacinaForm,
    TratamentoForm,
    VacinaLoteGerarForm,
)


class VacinaListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Vacina
    template_name = "sanidade/vacina_list.html"
    context_object_name = "vacinas"
    paginate_by = 20
    permission_required = "sanidade.view_vacina"
    search_fields = ["nome", "fabricante"]


class VacinaDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = Vacina
    template_name = "sanidade/vacina_detail.html"
    context_object_name = "vacina"
    permission_required = "sanidade.view_vacina"


def _regras_vacinas_lote():
    return [
        (1, "Vacina A"),
        (7, "Vacina B"),
        (14, "Vacina C"),
        (21, "Vacina D"),
    ]


def _gerar_vacinas_lote(lote, data_nascimento):
    if not data_nascimento:
        return
    for dias, nome in _regras_vacinas_lote():
        data_prevista = data_nascimento + timezone.timedelta(days=int(dias))
        VacinaLote.objects.get_or_create(
            lote=lote,
            nome_vacina=nome,
            data_prevista=data_prevista,
            defaults={"aplicada": False},
        )


class VacinaLoteListView(AdminManagerOrPermMixin, AuthenticatedView, generic.TemplateView):
    template_name = "sanidade/vacina_lote_list.html"
    permission_required = "sanidade.view_vacina"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lote_id = kwargs.get("pk")
        from lotes.models import Lote

        lote = Lote.objects.get(pk=lote_id)
        form = VacinaLoteGerarForm(self.request.GET or None)
        data_nascimento = None
        if form.is_valid():
            data_nascimento = form.cleaned_data["data_nascimento"]
        elif lote.data_criacao:
            data_nascimento = lote.data_criacao

        if data_nascimento:
            _gerar_vacinas_lote(lote, data_nascimento)

        vacinas = VacinaLote.objects.filter(lote=lote).order_by("data_prevista")
        ctx["lote"] = lote
        ctx["vacinas"] = vacinas
        ctx["form"] = form if form.is_bound else VacinaLoteGerarForm(initial={"data_nascimento": data_nascimento})
        ctx["hoje"] = timezone.localdate()
        return ctx


class VacinaLoteMarcarView(AdminManagerOrPermMixin, AuthenticatedView, generic.View):
    permission_required = "sanidade.change_vacinalote"

    def post(self, request, *args, **kwargs):
        from lotes.models import Lote

        lote = Lote.objects.get(pk=kwargs["pk"])
        vacina = VacinaLote.objects.get(pk=kwargs["vacina_id"], lote=lote)
        vacina.aplicada = True
        vacina.data_aplicacao = timezone.localdate()
        vacina.save()
        from django.shortcuts import redirect

        return redirect("sanidade:vacina_lote", pk=lote.pk)

class VacinaCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = Vacina
    form_class = VacinaForm
    template_name = "sanidade/vacina_form.html"
    success_url = reverse_lazy("sanidade:vacina_list")
    permission_required = "sanidade.add_vacina"


class VacinaUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = Vacina
    form_class = VacinaForm
    template_name = "sanidade/vacina_form.html"
    success_url = reverse_lazy("sanidade:vacina_list")
    permission_required = "sanidade.change_vacina"


class VacinaDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = Vacina
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("sanidade:vacina_list")
    permission_required = "sanidade.delete_vacina"


class MedicamentoListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):       
    model = Medicamento
    template_name = "sanidade/medicamento_list.html"
    context_object_name = "medicamentos"
    paginate_by = 20
    permission_required = "sanidade.view_medicamento"
    search_fields = ["nome", "categoria"]


class MedicamentoDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = Medicamento
    template_name = "sanidade/medicamento_detail.html"
    context_object_name = "medicamento"
    permission_required = "sanidade.view_medicamento"


class MedicamentoCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = Medicamento
    form_class = MedicamentoForm
    template_name = "sanidade/medicamento_form.html"
    success_url = reverse_lazy("sanidade:medicamento_list")
    permission_required = "sanidade.add_medicamento"


class MedicamentoUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = Medicamento
    form_class = MedicamentoForm
    template_name = "sanidade/medicamento_form.html"
    success_url = reverse_lazy("sanidade:medicamento_list")
    permission_required = "sanidade.change_medicamento"


class MedicamentoDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = Medicamento
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("sanidade:medicamento_list")
    permission_required = "sanidade.delete_medicamento"


class AplicacaoListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = AplicacaoVacina
    template_name = "sanidade/aplicacao_list.html"
    context_object_name = "aplicacoes"
    paginate_by = 20
    permission_required = "sanidade.view_aplicacaovacina"
    search_fields = ["vacina__nome", "observacoes"]
    filter_fields = ["status", "vacina"]

    def get_queryset(self):
        return super().get_queryset().select_related("vacina", "ave", "lote")


class AplicacaoCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = AplicacaoVacina
    form_class = AplicacaoVacinaForm
    template_name = "sanidade/aplicacao_form.html"
    success_url = reverse_lazy("sanidade:aplicacao_list")
    permission_required = "sanidade.add_aplicacaovacina"


class AplicacaoUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = AplicacaoVacina
    form_class = AplicacaoVacinaForm
    template_name = "sanidade/aplicacao_form.html"
    success_url = reverse_lazy("sanidade:aplicacao_list")
    permission_required = "sanidade.change_aplicacaovacina"


class AplicacaoDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = AplicacaoVacina
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("sanidade:aplicacao_list")
    permission_required = "sanidade.delete_aplicacaovacina"


class TratamentoListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Tratamento
    template_name = "sanidade/tratamento_list.html"
    context_object_name = "tratamentos"
    paginate_by = 20
    permission_required = "sanidade.view_tratamento"
    search_fields = ["doenca", "medicamento__nome"]

    def get_queryset(self):
        return super().get_queryset().select_related("medicamento", "ave", "lote")


class TratamentoCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = Tratamento
    form_class = TratamentoForm
    template_name = "sanidade/tratamento_form.html"
    success_url = reverse_lazy("sanidade:tratamento_list")
    permission_required = "sanidade.add_tratamento"


class TratamentoUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = Tratamento
    form_class = TratamentoForm
    template_name = "sanidade/tratamento_form.html"
    success_url = reverse_lazy("sanidade:tratamento_list")
    permission_required = "sanidade.change_tratamento"


class TratamentoDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = Tratamento
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("sanidade:tratamento_list")
    permission_required = "sanidade.delete_tratamento"

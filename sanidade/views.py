from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render

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


def _aplicacoes_queryset(request, queryset=None):
    def _param(name):
        return (request.GET.get(name) or request.POST.get(name) or "").strip()

    qs = (queryset or AplicacaoVacina.objects.all()).select_related("vacina", "ave", "lote")
    query = _param("q")
    if query:
        qs = qs.filter(Q(vacina__nome__icontains=query) | Q(observacoes__icontains=query))
    vacina = _param("vacina")
    if vacina:
        qs = qs.filter(vacina_id=vacina)
    status = _param("status")
    if status:
        qs = qs.filter(status=status)
    lote = _param("lote")
    if lote:
        qs = qs.filter(lote_id=lote)
    inicio = _param("inicio")
    fim = _param("fim")
    if inicio:
        qs = qs.filter(data_programada__gte=inicio)
    if fim:
        qs = qs.filter(data_programada__lte=fim)
    status_visual = _param("status_visual")
    atrasadas = _param("atrasadas")
    hoje = timezone.localdate()
    if status_visual == "atrasada" or atrasadas in {"1", "true", "True", "sim"}:
        qs = qs.filter(status=AplicacaoVacina.STATUS_PENDENTE, data_programada__lt=hoje)
    elif status_visual == "hoje":
        qs = qs.filter(status=AplicacaoVacina.STATUS_PENDENTE, data_programada=hoje)
    elif status_visual == "proxima":
        qs = qs.filter(
            status=AplicacaoVacina.STATUS_PENDENTE,
            data_programada__gt=hoje,
            data_programada__lte=hoje + timezone.timedelta(days=7),
        )
    return qs


def _aplicacao_body_context(request, queryset=None, paginate_by=20):
    aplicacoes_qs = _aplicacoes_queryset(request, queryset)
    page_number = request.GET.get("page") or request.POST.get("page")
    paginator = Paginator(aplicacoes_qs, paginate_by)
    page_obj = paginator.get_page(page_number)
    aplicacoes = page_obj.object_list

    resumo_por_lote = {}
    for aplicacao in aplicacoes_qs:
        chave = aplicacao.lote.nome if aplicacao.lote else "Sem lote"
        if chave not in resumo_por_lote:
            resumo_por_lote[chave] = {"nome": chave, "pendentes": 0, "aplicadas": 0, "atrasadas": 0}
        if aplicacao.status == AplicacaoVacina.STATUS_APLICADA:
            resumo_por_lote[chave]["aplicadas"] += 1
        elif aplicacao.atrasada:
            resumo_por_lote[chave]["atrasadas"] += 1
        else:
            resumo_por_lote[chave]["pendentes"] += 1

    hoje = timezone.localdate()
    return {
        "aplicacoes": aplicacoes,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "total_pendentes": aplicacoes_qs.filter(status=AplicacaoVacina.STATUS_PENDENTE).count(),
        "total_aplicadas": aplicacoes_qs.filter(status=AplicacaoVacina.STATUS_APLICADA).count(),
        "total_atrasadas": aplicacoes_qs.filter(
            status=AplicacaoVacina.STATUS_PENDENTE,
            data_programada__lt=hoje,
        ).count(),
        "total_hoje": aplicacoes_qs.filter(
            status=AplicacaoVacina.STATUS_PENDENTE,
            data_programada=hoje,
        ).count(),
        "resumo_por_lote": sorted(
            resumo_por_lote.values(),
            key=lambda item: (item["atrasadas"], item["pendentes"], item["nome"]),
            reverse=True,
        )[:6],
    }


def _vacina_lote_payload(request, lote):
    form = VacinaLoteGerarForm(request.GET or None)
    data_nascimento = None
    if form.is_valid():
        data_nascimento = form.cleaned_data["data_nascimento"]
    elif lote.data_criacao:
        data_nascimento = lote.data_criacao

    if data_nascimento:
        _gerar_vacinas_lote(lote, data_nascimento)

    vacinas_base = list(VacinaLote.objects.filter(lote=lote).order_by("data_prevista"))
    status = request.GET.get("status", "").strip()
    nome = request.GET.get("vacina", "").strip().lower()
    inicio = request.GET.get("inicio", "").strip()
    fim = request.GET.get("fim", "").strip()
    vacinas = vacinas_base
    if status:
        vacinas = [v for v in vacinas if v.status_operacional == status]
    if nome:
        vacinas = [v for v in vacinas if nome in (v.nome_vacina or "").lower()]
    if inicio:
        vacinas = [v for v in vacinas if str(v.data_prevista) >= inicio]
    if fim:
        vacinas = [v for v in vacinas if str(v.data_prevista) <= fim]

    hoje = timezone.localdate()
    proximas = sorted(
        [v for v in vacinas_base if not v.aplicada and v.data_prevista and v.data_prevista >= hoje],
        key=lambda item: item.data_prevista,
    )[:5]
    return {
        "vacinas": vacinas,
        "form": form if form.is_bound else VacinaLoteGerarForm(initial={"data_nascimento": data_nascimento}),
        "hoje": hoje,
        "vacinas_total": len(vacinas_base),
        "vacinas_pendentes": sum(1 for v in vacinas_base if v.status_operacional == "pendente"),
        "vacinas_aplicadas": sum(1 for v in vacinas_base if v.aplicada),
        "vacinas_atrasadas": sum(1 for v in vacinas_base if v.atrasada),
        "vacinas_hoje": sum(1 for v in vacinas_base if v.prevista_hoje),
        "proximas_vacinas": proximas,
        "vacinas_pendentes_lote": [v for v in vacinas_base if not v.aplicada][:5],
    }


class VacinaLoteListView(AdminManagerOrPermMixin, AuthenticatedView, generic.TemplateView):
    template_name = "sanidade/vacina_lote_list.html"
    permission_required = "sanidade.view_vacina"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lote_id = kwargs.get("pk")
        from lotes.models import Lote

        lote = Lote.objects.get(pk=lote_id)
        ctx["lote"] = lote
        ctx.update(_vacina_lote_payload(self.request, lote))
        return ctx


class VacinaLoteMarcarView(AdminManagerOrPermMixin, AuthenticatedView, generic.View):
    permission_required = "sanidade.change_vacinalote"

    def post(self, request, *args, **kwargs):
        from lotes.models import Lote

        lote = Lote.objects.get(pk=kwargs["pk"])
        vacina = VacinaLote.objects.get(pk=kwargs["vacina_id"], lote=lote)
        vacina.aplicada = True
        vacina.data_aplicacao = vacina.data_aplicacao or timezone.localdate()
        vacina.save()
        from django.shortcuts import redirect
        messages.success(request, f"{vacina.nome_vacina} marcada como aplicada.")

        return redirect("sanidade:vacina_lote", pk=lote.pk)


class VacinaLoteBulkMarcarView(AdminManagerOrPermMixin, AuthenticatedView, generic.View):
    permission_required = "sanidade.change_vacinalote"

    def post(self, request, *args, **kwargs):
        from lotes.models import Lote
        from django.shortcuts import redirect

        lote = Lote.objects.get(pk=kwargs["pk"])
        ids = request.POST.getlist("vacina_ids")
        if not ids:
            messages.warning(request, "Selecione ao menos uma vacina para marcar como aplicada.")
            return redirect("sanidade:vacina_lote", pk=lote.pk)

        atualizadas = (
            VacinaLote.objects.filter(lote=lote, pk__in=ids, aplicada=False)
            .update(aplicada=True, data_aplicacao=timezone.localdate())
        )
        if atualizadas:
            messages.success(request, f"{atualizadas} vacina(s) marcadas como aplicadas.")
        else:
            messages.info(request, "Nenhuma vacina pendente foi atualizada.")
        return redirect("sanidade:vacina_lote", pk=lote.pk)


class VacinaLotePrintView(AdminManagerOrPermMixin, AuthenticatedView, generic.TemplateView):
    template_name = "sanidade/vacina_lote_print.html"
    permission_required = "sanidade.view_vacina"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from lotes.models import Lote

        lote = Lote.objects.get(pk=kwargs["pk"])
        ctx["lote"] = lote
        ctx.update(_vacina_lote_payload(self.request, lote))
        return ctx

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

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true":
            return ["sanidade/_aplicacao_body.html"]
        return [self.template_name]

    def get_queryset(self):
        return _aplicacoes_queryset(self.request, super().get_queryset())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from lotes.models import Lote
        ctx.update(_aplicacao_body_context(self.request, self.get_queryset(), self.paginate_by))

        ctx.update(
            {
                "vacinas_filtro": Vacina.objects.order_by("nome"),
                "lotes_filtro": Lote.objects.order_by("nome"),
            }
        )
        return ctx


class AplicacaoQuickApplyView(AdminManagerOrPermMixin, AuthenticatedView, generic.View):
    permission_required = "sanidade.change_aplicacaovacina"

    def post(self, request, *args, **kwargs):
        aplicacao = AplicacaoVacina.objects.get(pk=kwargs["pk"])
        aplicacao.status = AplicacaoVacina.STATUS_APLICADA
        aplicacao.data_aplicacao = aplicacao.data_aplicacao or timezone.localdate()
        aplicacao.save()
        from django.shortcuts import redirect

        messages.success(request, f"{aplicacao.vacina} marcada como aplicada.")
        if request.headers.get("HX-Request") == "true":
            ctx = _aplicacao_body_context(request, None, paginate_by=20)
            return render(request, "sanidade/_aplicacao_body.html", ctx)
        return redirect("sanidade:aplicacao_list")


class AplicacaoPrintView(AdminManagerOrPermMixin, AuthenticatedView, generic.TemplateView):
    template_name = "sanidade/aplicacao_print.html"
    permission_required = "sanidade.view_aplicacaovacina"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        aplicacoes = list(_aplicacoes_queryset(self.request))
        hoje = timezone.localdate()
        ctx.update(
            {
                "aplicacoes": aplicacoes,
                "hoje": hoje,
                "total_pendentes": sum(1 for item in aplicacoes if item.status == AplicacaoVacina.STATUS_PENDENTE),
                "total_aplicadas": sum(1 for item in aplicacoes if item.status == AplicacaoVacina.STATUS_APLICADA),
                "total_atrasadas": sum(1 for item in aplicacoes if item.atrasada),
                "total_hoje": sum(1 for item in aplicacoes if item.prevista_hoje),
            }
        )
        return ctx


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
        qs = super().get_queryset().select_related("medicamento", "ave", "lote")
        alvo = self.request.GET.get("alvo", "").strip()
        if alvo == "ave":
            qs = qs.filter(ave__isnull=False)
        elif alvo == "lote":
            qs = qs.filter(lote__isnull=False)
        carencia = self.request.GET.get("carencia", "").strip()
        hoje = timezone.localdate()
        if carencia == "ativa":
            qs = qs.filter(data_fim__isnull=False, data_fim__gte=hoje - timezone.timedelta(days=3650))
            qs = [t.pk for t in qs if t.carencia_ativa]
            return Tratamento.objects.filter(pk__in=qs).select_related("medicamento", "ave", "lote")
        status = self.request.GET.get("status_tratamento", "").strip()
        if status == "ativo":
            qs = qs.filter(Q(data_fim__isnull=True) | Q(data_fim__gte=hoje))
        elif status == "finalizado":
            qs = qs.filter(data_fim__lt=hoje)
        inicio = self.request.GET.get("inicio", "").strip()
        fim = self.request.GET.get("fim", "").strip()
        if inicio:
            qs = qs.filter(data_inicio__gte=inicio)
        if fim:
            qs = qs.filter(data_inicio__lte=fim)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base = Tratamento.objects.select_related("medicamento", "ave", "lote")
        hoje = timezone.localdate()
        ativos = base.filter(Q(data_fim__isnull=True) | Q(data_fim__gte=hoje)).count()
        finalizados = base.filter(data_fim__lt=hoje).count()
        carencias_ativas = sum(1 for t in base if t.carencia_ativa)
        ctx.update(
            {
                "tratamentos_ativos_count": ativos,
                "tratamentos_finalizados_count": finalizados,
                "tratamentos_carencia_count": carencias_ativas,
            }
        )
        return ctx


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

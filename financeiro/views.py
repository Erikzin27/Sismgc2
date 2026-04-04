from datetime import date, datetime
from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages
from django.db.models import Count, Max, Q, Sum
from django.db.models.functions import TruncMonth

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin
from .models import LancamentoFinanceiro, OrcamentoFuturo
from .forms import LancamentoFinanceiroForm, OrcamentoFuturoForm


class LancamentoListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = LancamentoFinanceiro
    template_name = "financeiro/lancamento_list.html"
    context_object_name = "lancamentos"
    paginate_by = 20
    permission_required = "financeiro.view_lancamentofinanceiro"
    search_fields = ["descricao"]
    filter_fields = ["tipo", "categoria"]

    def get_queryset(self):
        return super().get_queryset().select_related("lote", "ave", "venda")


class LancamentoDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = LancamentoFinanceiro
    template_name = "financeiro/lancamento_detail.html"
    context_object_name = "lancamento"
    permission_required = "financeiro.view_lancamentofinanceiro"

    def get_queryset(self):
        return super().get_queryset().select_related("lote", "ave", "venda")


class LancamentoCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = LancamentoFinanceiro
    form_class = LancamentoFinanceiroForm
    template_name = "financeiro/lancamento_form.html"
    success_url = reverse_lazy("financeiro:list")
    permission_required = "financeiro.add_lancamentofinanceiro"

    def form_valid(self, form):
        messages.success(self.request, "Lançamento criado com sucesso.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar. Verifique os campos destacados.")
        return super().form_invalid(form)


class LancamentoUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = LancamentoFinanceiro
    form_class = LancamentoFinanceiroForm
    template_name = "financeiro/lancamento_form.html"
    success_url = reverse_lazy("financeiro:list")
    permission_required = "financeiro.change_lancamentofinanceiro"

    def form_valid(self, form):
        messages.success(self.request, "Lançamento atualizado com sucesso.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar. Verifique os campos destacados.")
        return super().form_invalid(form)


class LancamentoDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):    
    model = LancamentoFinanceiro
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("financeiro:list")
    permission_required = "financeiro.delete_lancamentofinanceiro"


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _caixa_atual_granja():
    totais = LancamentoFinanceiro.objects.aggregate(
        entradas=Sum("valor", filter=Q(tipo=LancamentoFinanceiro.TIPO_ENTRADA)),
        saidas=Sum("valor", filter=Q(tipo=LancamentoFinanceiro.TIPO_SAIDA)),
    )
    entradas = totais["entradas"] or 0
    saidas = totais["saidas"] or 0
    return entradas - saidas


class FinanceiroDashboardView(AdminManagerOrPermMixin, AuthenticatedView, generic.TemplateView):
    template_name = "financeiro/dashboard.html"
    permission_required = "financeiro.view_lancamentofinanceiro"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        inicio = _parse_date(self.request.GET.get("inicio"))
        fim = _parse_date(self.request.GET.get("fim"))
        tipo = self.request.GET.get("tipo") or ""
        categoria = self.request.GET.get("categoria") or ""
        lote = self.request.GET.get("lote") or ""

        qs = LancamentoFinanceiro.objects.select_related("lote", "ave", "venda")
        if inicio:
            qs = qs.filter(data__gte=inicio)
        if fim:
            qs = qs.filter(data__lte=fim)
        if tipo:
            qs = qs.filter(tipo=tipo)
        if categoria:
            qs = qs.filter(categoria=categoria)
        if lote:
            qs = qs.filter(lote__id=lote)

        entradas = qs.filter(tipo=LancamentoFinanceiro.TIPO_ENTRADA)
        saidas = qs.filter(tipo=LancamentoFinanceiro.TIPO_SAIDA)
        totais_periodo = qs.aggregate(
            total_entradas=Sum("valor", filter=Q(tipo=LancamentoFinanceiro.TIPO_ENTRADA)),
            total_saidas=Sum("valor", filter=Q(tipo=LancamentoFinanceiro.TIPO_SAIDA)),
            total_lancamentos=Count("id"),
        )
        total_entradas = totais_periodo["total_entradas"] or 0
        total_saidas = totais_periodo["total_saidas"] or 0
        saldo_atual = total_entradas - total_saidas

        hoje = date.today()
        mes_inicio = hoje.replace(day=1)
        totais_mes = LancamentoFinanceiro.objects.aggregate(
            entradas_mes=Sum(
                "valor",
                filter=Q(tipo=LancamentoFinanceiro.TIPO_ENTRADA, data__gte=mes_inicio),
            ),
            saidas_mes=Sum(
                "valor",
                filter=Q(tipo=LancamentoFinanceiro.TIPO_SAIDA, data__gte=mes_inicio),
            ),
        )
        entradas_mes = totais_mes["entradas_mes"] or 0
        saidas_mes = totais_mes["saidas_mes"] or 0
        saldo_mes = entradas_mes - saidas_mes

        maior_entrada = entradas.order_by("-valor").first()
        maior_saida = saidas.order_by("-valor").first()
        recentes = qs.order_by("-data", "-created_at")[:10]

        # Agrupa por mês do período filtrado; quando não houver filtro, mostra os últimos 6 meses.
        base_chart_qs = qs
        if not inicio and not fim:
            hoje = date.today()
            limite = date(hoje.year, max(hoje.month - 5, 1), 1)
            if hoje.month <= 5:
                limite = date(hoje.year - 1, 12 + hoje.month - 5, 1)
            base_chart_qs = qs.filter(data__gte=limite)

        por_mes = (
            base_chart_qs.annotate(periodo=TruncMonth("data"))
            .values("periodo", "tipo")
            .annotate(total=Sum("valor"))
            .order_by("periodo", "tipo")
        )

        meses = []
        for row in por_mes:
            periodo = row["periodo"]
            if periodo and periodo not in meses:
                meses.append(periodo)

        labels = [mes.strftime("%b/%y").capitalize() for mes in meses]
        series_entradas = []
        series_saidas = []
        for mes in meses:
            total_e = next(
                (
                    row["total"]
                    for row in por_mes
                    if row["periodo"] == mes and row["tipo"] == LancamentoFinanceiro.TIPO_ENTRADA
                ),
                0,
            ) or 0
            total_s = next(
                (
                    row["total"]
                    for row in por_mes
                    if row["periodo"] == mes and row["tipo"] == LancamentoFinanceiro.TIPO_SAIDA
                ),
                0,
            ) or 0
            series_entradas.append(float(total_e))
            series_saidas.append(float(total_s))

        ctx.update(
            {
                "total_entradas": total_entradas,
                "total_saidas": total_saidas,
                "saldo_atual": saldo_atual,
                "caixa_atual": saldo_atual,
                "total_lancamentos": totais_periodo["total_lancamentos"] or 0,
                "entradas_mes": entradas_mes,
                "saidas_mes": saidas_mes,
                "saldo_mes": saldo_mes,
                "maior_entrada": maior_entrada,
                "maior_saida": maior_saida,
                "recentes": recentes,
                "categorias": LancamentoFinanceiro.CATEGORIAS,
                "labels_mes": labels,
                "series_entradas": series_entradas,
                "series_saidas": series_saidas,
                "chart_totais": [float(total_entradas), float(total_saidas)],
            }
        )
        return ctx


class OrcamentoFuturoListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = OrcamentoFuturo
    template_name = "financeiro/orcamento_list.html"
    context_object_name = "orcamentos"
    paginate_by = 20
    permission_required = "financeiro.view_orcamentofuturo"
    search_fields = ["titulo", "descricao", "categoria", "observacoes"]
    filter_fields = ["status", "prioridade", "ativo"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        caixa_atual = _caixa_atual_granja()
        queryset = self.object_list
        for orcamento in ctx["orcamentos"]:
            orcamento.caixa_atual_referencia = caixa_atual
            faltante = orcamento.valor_previsto - caixa_atual
            orcamento.valor_faltante = faltante if faltante > 0 else 0

        resumo = queryset.aggregate(
            total_orcamentos=Count("id"),
            soma_planejada=Sum("valor_previsto"),
            maior_valor=Max("valor_previsto"),
            concluidos=Count("id", filter=Q(status=OrcamentoFuturo.STATUS_CONCLUIDO)),
            em_andamento=Count("id", filter=Q(status=OrcamentoFuturo.STATUS_ANDAMENTO)),
            planejados=Count("id", filter=Q(status=OrcamentoFuturo.STATUS_PLANEJADO)),
        )

        ctx.update(
            {
                "caixa_atual_referencia": caixa_atual,
                "total_orcamentos": resumo["total_orcamentos"] or 0,
                "soma_planejada": resumo["soma_planejada"] or 0,
                "maior_orcamento": queryset.order_by("-valor_previsto").first(),
                "concluidos": resumo["concluidos"] or 0,
                "em_andamento": resumo["em_andamento"] or 0,
                "planejados": resumo["planejados"] or 0,
            }
        )
        return ctx


class OrcamentoFuturoDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = OrcamentoFuturo
    template_name = "financeiro/orcamento_detail.html"
    context_object_name = "orcamento"
    permission_required = "financeiro.view_orcamentofuturo"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        caixa_atual = _caixa_atual_granja()
        valor_faltante = self.object.valor_previsto - caixa_atual
        ctx["caixa_atual_referencia"] = caixa_atual
        ctx["valor_faltante"] = valor_faltante if valor_faltante > 0 else 0
        return ctx


class OrcamentoFuturoCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = OrcamentoFuturo
    form_class = OrcamentoFuturoForm
    template_name = "financeiro/orcamento_form.html"
    success_url = reverse_lazy("financeiro:orcamento_list")
    permission_required = "financeiro.add_orcamentofuturo"

    def form_valid(self, form):
        messages.success(self.request, "Orçamento salvo com sucesso.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar o orçamento. Verifique os campos destacados.")
        return super().form_invalid(form)


class OrcamentoFuturoUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = OrcamentoFuturo
    form_class = OrcamentoFuturoForm
    template_name = "financeiro/orcamento_form.html"
    success_url = reverse_lazy("financeiro:orcamento_list")
    permission_required = "financeiro.change_orcamentofuturo"

    def form_valid(self, form):
        messages.success(self.request, "Orçamento atualizado com sucesso.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar o orçamento. Verifique os campos destacados.")
        return super().form_invalid(form)


class OrcamentoFuturoDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = OrcamentoFuturo
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("financeiro:orcamento_list")
    permission_required = "financeiro.delete_orcamentofuturo"

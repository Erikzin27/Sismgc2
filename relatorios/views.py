from datetime import datetime
from decimal import Decimal
from io import BytesIO
from django.http import HttpResponse
from django.contrib import messages
from django.views.generic import TemplateView
from django.template.loader import render_to_string
from django.db.models import F, Prefetch, Sum
from django.templatetags.static import static
from django.contrib.staticfiles import finders
from core.mixins import AuthenticatedView, ManagerOrAdminMixin
from core.services.config import get_configuracao_sistema
from aves.models import Ave
from linhagens.models import Linhagem
from lotes.models import Lote
from sanidade.models import AplicacaoVacina, Tratamento
from financeiro.models import LancamentoFinanceiro
from incubacao.models import Incubacao
from estoque.models import ItemEstoque, MovimentoEstoque
from nascimentos.models import Nascimento
from vendas.models import Venda


REPORT_LABELS = {
    "lotes": "Relatorio de Lotes",
    "aves": "Relatorio de Aves",
    "vacinas": "Relatorio de Vacinacao",
    "financeiro": "Relatorio Financeiro",
    "incubacao": "Relatorio de Incubacao",
    "estoque_baixo": "Relatorio de Estoque Baixo",
    "consumo_periodo": "Consumo por Periodo",
    "consumo_lote": "Consumo por Lote",
    "perdas": "Relatorio de Perdas",
    "reproducao": "Relatorio de Reproducao",
    "consumo_custo_lote": "Consumo e Custo por Lote",
    "previsao_estoque": "Previsao de Estoque",
    "comparacao_lotes": "Comparacao entre Lotes",
    "lucro_lote": "Lucro por Lote",
    "ranking_lotes": "Ranking de Lotes",
    "ranking_reprodutores": "Ranking de Reprodutores e Matrizes",
}


def _report_label(report):
    return REPORT_LABELS.get(report, f"Relatorio: {report}")


def _format_filter_period(inicio=None, fim=None):
    if inicio and fim:
        return f"{inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
    if inicio:
        return f"A partir de {inicio.strftime('%d/%m/%Y')}"
    if fim:
        return f"Ate {fim.strftime('%d/%m/%Y')}"
    return "Periodo total"


def _safe_decimal(value):
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _build_report_meta(report, data, inicio=None, fim=None):
    config = get_configuracao_sistema()
    nome_granja = config.nome_granja or config.nome_sistema or "SISMGC"
    resumo = []

    if report == "lotes":
        lotes = list(data.get("lotes", []))
        resumo = [
            ("Lotes", len(lotes)),
            ("Aves atuais", sum((l.quantidade_atual or 0) for l in lotes)),
            ("Custo total", f"R$ {sum((_safe_decimal(l.custo_acumulado) for l in lotes), Decimal('0'))}"),
        ]
    elif report == "aves":
        aves = list(data.get("aves", []))
        resumo = [
            ("Aves", len(aves)),
            ("Ativas", sum(1 for a in aves if getattr(a, "status", "") == getattr(Ave, "STATUS_ATIVA", "ativa"))),
            ("Reproducao", sum(1 for a in aves if getattr(a, "finalidade", "") == getattr(Ave, "FINALIDADE_REPRODUCAO", "reproducao"))),
        ]
    elif report == "vacinas":
        vacinas = list(data.get("vacinas", []))
        resumo = [
            ("Aplicacoes", len(vacinas)),
            ("Pendentes", sum(1 for v in vacinas if getattr(v, "status", "") == getattr(AplicacaoVacina, "STATUS_PENDENTE", "pendente"))),
            ("Concluidas", sum(1 for v in vacinas if getattr(v, "status", "") == getattr(AplicacaoVacina, "STATUS_APLICADA", "ok"))),
        ]
    elif report == "financeiro":
        lancamentos = list(data.get("lancamentos", []))
        entradas = sum((_safe_decimal(l.valor) for l in lancamentos if l.tipo == LancamentoFinanceiro.TIPO_ENTRADA), Decimal("0"))
        saidas = sum((_safe_decimal(l.valor) for l in lancamentos if l.tipo == LancamentoFinanceiro.TIPO_SAIDA), Decimal("0"))
        resumo = [("Entradas", f"R$ {entradas}"), ("Saidas", f"R$ {saidas}"), ("Saldo", f"R$ {entradas - saidas}")]
    elif report == "incubacao":
        incubacoes = list(data.get("incubacoes", []))
        ovos = sum((i.quantidade_ovos or 0) for i in incubacoes)
        nascidos = sum((i.quantidade_nascida or 0) for i in incubacoes)
        resumo = [("Incubacoes", len(incubacoes)), ("Ovos", ovos), ("Nascidos", nascidos)]
    elif report == "estoque_baixo":
        itens = list(data.get("itens", []))
        resumo = [("Itens criticos", len(itens))]
    elif report == "reproducao":
        incubacoes = list(data.get("incubacoes", []))
        ovos = sum((i.quantidade_ovos or 0) for i in incubacoes)
        nascidos = sum((i.quantidade_nascida or 0) for i in incubacoes)
        perdas = sum((i.perdas or 0) for i in incubacoes)
        taxa = (Decimal(nascidos) / Decimal(ovos) * 100) if ovos else Decimal("0")
        resumo = [("Incubacoes", len(incubacoes)), ("Nascidos", nascidos), ("Taxa", f"{taxa.quantize(Decimal('0.01'))}%")]
    elif report in {"consumo_custo_lote", "comparacao_lotes", "lucro_lote"}:
        linhas = list(data.get("linhas_lote", []))
        resumo = [
            ("Lotes", len(linhas)),
            ("Consumo", f"{sum((_safe_decimal(l['consumo_racao_total']) for l in linhas), Decimal('0'))} kg"),
            ("Lucro", f"R$ {sum((_safe_decimal(l['lucro_final']) for l in linhas), Decimal('0'))}"),
        ]
    elif report == "previsao_estoque":
        itens = list(data.get("itens_previsao", []))
        resumo = [("Itens", len(itens)), ("Reposicao proxima", sum(1 for i in itens if i["reposicao_proxima"]))]
    elif report == "ranking_lotes":
        ranking = list(data.get("ranking_lotes", []))
        topo = str(ranking[0]["lote"]) if ranking else "-"
        resumo = [("Lotes ranqueados", len(ranking)), ("Melhor lote", topo)]
    elif report == "ranking_reprodutores":
        ranking = list(data.get("ranking_reprodutores", []))
        topo = str(ranking[0]["ave"]) if ranking else "-"
        resumo = [("Aves ranqueadas", len(ranking)), ("Melhor ave", topo)]

    return {
        "titulo_relatorio": _report_label(report),
        "nome_granja_pdf": nome_granja,
        "logo_pdf_url": static(config.logo_ativa) if getattr(config, "logo_ativa", "") else "",
        "logo_pdf_path": finders.find(config.logo_ativa) if getattr(config, "logo_ativa", "") else None,
        "filtros_pdf": [
            ("Periodo", _format_filter_period(inicio, fim)),
        ],
        "resumo_pdf": resumo,
        "gerado_em_pdf": datetime.now(),
    }


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _filtered_lotes(inicio=None, fim=None):
    lotes = (
        Lote.objects.select_related("linhagem_principal")
        .prefetch_related(
            Prefetch(
                "movimentoestoque_set",
                queryset=MovimentoEstoque.objects.select_related("item").only(
                    "data",
                    "tipo",
                    "quantidade",
                    "custo_unitario",
                    "lote_relacionado_id",
                    "item__categoria",
                ),
                to_attr="movimentos_prefetch",
            ),
            Prefetch(
                "vendas",
                queryset=Venda.objects.only("data", "valor_total", "lote_id", "produto", "cliente"),
                to_attr="vendas_prefetch",
            ),
            Prefetch(
                "lancamentos",
                queryset=LancamentoFinanceiro.objects.only("data", "tipo", "categoria", "valor", "lote_id"),
                to_attr="lancamentos_prefetch",
            ),
        )
    )
    if inicio:
        lotes = lotes.filter(data_criacao__gte=inicio)
    if fim:
        lotes = lotes.filter(data_criacao__lte=fim)
    return lotes


def _build_lote_metric_row(lote):
    zero = Decimal("0")
    movimentos = getattr(lote, "movimentos_prefetch", [])
    vendas = getattr(lote, "vendas_prefetch", [])
    lancamentos = getattr(lote, "lancamentos_prefetch", [])

    movimentos_racao = [
        mov
        for mov in movimentos
        if getattr(getattr(mov, "item", None), "categoria", None) == ItemEstoque.CAT_RACAO
    ]
    consumo_racao = sum(
        (mov.quantidade or zero)
        for mov in movimentos_racao
        if mov.tipo == MovimentoEstoque.TIPO_SAIDA
    )
    custo_racao = sum((mov.custo_unitario or zero) for mov in movimentos_racao)
    despesas_extras = sum(
        (lanc.valor or zero)
        for lanc in lancamentos
        if lanc.tipo == LancamentoFinanceiro.TIPO_SAIDA
    )
    custo_sanitario = sum(
        (lanc.valor or zero)
        for lanc in lancamentos
        if lanc.tipo == LancamentoFinanceiro.TIPO_SAIDA
        and lanc.categoria in {LancamentoFinanceiro.CAT_VACINA, LancamentoFinanceiro.CAT_MEDICAMENTO}
    )
    receita_vendas = sum((venda.valor_total or zero) for venda in vendas)
    lucro_final = receita_vendas - (custo_racao + despesas_extras)
    mortalidade = lote.mortalidade_percentual
    conversao = (consumo_racao / lote.quantidade_inicial) if lote.quantidade_inicial else zero

    return {
        "lote": lote,
        "quantidade_atual": lote.quantidade_atual or 0,
        "custo_acumulado": lote.custo_acumulado or zero,
        "consumo_racao_total": consumo_racao,
        "custo_racao": custo_racao,
        "custo_sanitario": custo_sanitario,
        "despesas_extras": despesas_extras,
        "receita_vendas": receita_vendas,
        "lucro_final": lucro_final,
        "mortalidade_percentual": mortalidade,
        "conversao_alimentar": conversao,
        "reprodutivo": lote.reprodutivo,
        "status_reprodutivo": lote.status_reprodutivo,
        "status_reprodutivo_display": lote.get_status_reprodutivo_display() if lote.reprodutivo else "",
    }


def _report_context(report, inicio=None, fim=None):
    inicio = _parse_date(inicio)
    fim = _parse_date(fim)
    if report == "lotes":
        qs = Lote.objects.all()
        if inicio:
            qs = qs.filter(data_criacao__gte=inicio)
        if fim:
            qs = qs.filter(data_criacao__lte=fim)
        return {"lotes": qs}
    if report == "aves":
        qs = Ave.objects.all()
        if inicio:
            qs = qs.filter(data_nascimento__gte=inicio)
        if fim:
            qs = qs.filter(data_nascimento__lte=fim)
        return {"aves": qs}
    if report == "vacinas":
        qs = AplicacaoVacina.objects.all()
        if inicio:
            qs = qs.filter(data_programada__gte=inicio)
        if fim:
            qs = qs.filter(data_programada__lte=fim)
        return {"vacinas": qs}
    if report == "financeiro":
        qs = LancamentoFinanceiro.objects.all()
        if inicio:
            qs = qs.filter(data__gte=inicio)
        if fim:
            qs = qs.filter(data__lte=fim)
        return {"lancamentos": qs}
    if report == "incubacao":
        qs = Incubacao.objects.all()
        if inicio:
            qs = qs.filter(data_entrada__gte=inicio)
        if fim:
            qs = qs.filter(data_entrada__lte=fim)
        return {"incubacoes": qs}
    if report == "estoque_baixo":
        return {"itens": ItemEstoque.objects.filter(quantidade_atual__lte=F("estoque_minimo"))}
    if report == "consumo_periodo":
        qs = MovimentoEstoque.objects.filter(
            tipo=MovimentoEstoque.TIPO_SAIDA,
            item__categoria=ItemEstoque.CAT_RACAO,
        )
        if inicio:
            qs = qs.filter(data__gte=inicio)
        if fim:
            qs = qs.filter(data__lte=fim)
        return {"movimentos": qs}
    if report == "consumo_lote":
        qs = MovimentoEstoque.objects.filter(
            tipo=MovimentoEstoque.TIPO_SAIDA,
            item__categoria=ItemEstoque.CAT_RACAO,
            lote_relacionado__isnull=False,
        )
        if inicio:
            qs = qs.filter(data__gte=inicio)
        if fim:
            qs = qs.filter(data__lte=fim)
        return {"movimentos": qs}
    if report == "perdas":
        qs = MovimentoEstoque.objects.filter(motivo=MovimentoEstoque.MOTIVO_DESCARTE)
        if inicio:
            qs = qs.filter(data__gte=inicio)
        if fim:
            qs = qs.filter(data__lte=fim)
        return {"movimentos": qs}
    if report == "reproducao":
        incubacoes = Incubacao.objects.select_related("lote_relacionado", "matriz_responsavel__linhagem").all()
        if inicio:
            incubacoes = incubacoes.filter(data_entrada__gte=inicio)
        if fim:
            incubacoes = incubacoes.filter(data_entrada__lte=fim)
        return {"incubacoes": incubacoes}
    if report == "consumo_custo_lote":
        lotes = _filtered_lotes(inicio, fim)
        return {"linhas_lote": [_build_lote_metric_row(lote) for lote in lotes]}
    if report == "previsao_estoque":
        itens = []
        base_itens = ItemEstoque.objects.prefetch_related(
            Prefetch(
                "movimentacoes",
                queryset=MovimentoEstoque.objects.only("item_id", "data", "tipo", "quantidade"),
                to_attr="movimentacoes_prefetch",
            )
        )
        for item in base_itens:
            movimentos = [
                mov
                for mov in getattr(item, "movimentacoes_prefetch", [])
                if mov.tipo == MovimentoEstoque.TIPO_SAIDA
                and (not inicio or mov.data >= inicio)
                and (not fim or mov.data <= fim)
            ]
            total_consumido = sum((mov.quantidade or 0) for mov in movimentos)
            dias_base = 30
            if inicio and fim and fim >= inicio:
                dias_base = max((fim - inicio).days + 1, 1)
            consumo_medio = total_consumido / dias_base if dias_base else 0
            duracao_estimada = 0
            if consumo_medio:
                duracao_estimada = float(item.quantidade_atual) / float(consumo_medio)
            itens.append(
                {
                    "item": item,
                    "consumo_medio": consumo_medio,
                    "duracao_estimada": duracao_estimada,
                    "reposicao_proxima": bool(duracao_estimada and duracao_estimada <= 15),
                }
            )
        return {"itens_previsao": itens}
    if report == "comparacao_lotes":
        lotes = _filtered_lotes(inicio, fim)
        return {"linhas_lote": [_build_lote_metric_row(lote) for lote in lotes]}
    if report == "lucro_lote":
        lotes = _filtered_lotes(inicio, fim)
        return {"linhas_lote": [_build_lote_metric_row(lote) for lote in lotes]}
    if report == "ranking_lotes":
        lotes = [_build_lote_metric_row(lote) for lote in _filtered_lotes(inicio, fim)]
        ranking = sorted(
            lotes,
            key=lambda linha: (
                float(linha["lucro_final"] or 0),
                -float(linha["mortalidade_percentual"] or 0),
                -float(linha["conversao_alimentar"] or 0),
            ),
            reverse=True,
        )
        return {"ranking_lotes": ranking}
    if report == "ranking_reprodutores":
        aves_reprodutivas = Ave.objects.filter(finalidade=Ave.FINALIDADE_REPRODUCAO).prefetch_related(
            "filhos_pai",
            "filhos_mae",
            "incubacoes_matriz",
        )
        ranking = []
        for ave in aves_reprodutivas:
            filhos = len(ave.filhos_pai.all()) + len(ave.filhos_mae.all())
            incubacoes_lista = list(ave.incubacoes_matriz.all()) if hasattr(ave, "incubacoes_matriz") else []
            incubacoes = len(incubacoes_lista)
            nascidos = sum((inc.quantidade_nascida or 0) for inc in incubacoes_lista)
            eficiencia = (nascidos / incubacoes) if incubacoes else filhos
            ranking.append(
                {
                    "ave": ave,
                    "filhos": filhos,
                    "incubacoes": incubacoes,
                    "nascidos": nascidos,
                    "eficiencia": eficiencia,
                }
            )
        ranking.sort(key=lambda item: (item["nascidos"], item["filhos"], item["eficiencia"]), reverse=True)
        return {"ranking_reprodutores": ranking}
    return {}


try:
    import openpyxl
except Exception:
    openpyxl = None


class SensitiveReportView(ManagerOrAdminMixin, AuthenticatedView, TemplateView):
    raise_exception = True


class RelatoriosHomeView(SensitiveReportView):
    template_name = "relatorios/index.html"


class RelatorioLoteView(SensitiveReportView):
    template_name = "relatorios/relatorio_lote.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("lotes", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioAveView(SensitiveReportView):
    template_name = "relatorios/relatorio_ave.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("aves", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioVacinaView(SensitiveReportView):
    template_name = "relatorios/relatorio_vacina.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("vacinas", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioFinanceiroView(SensitiveReportView):
    template_name = "relatorios/relatorio_financeiro.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("financeiro", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioIncubacaoView(SensitiveReportView):
    template_name = "relatorios/relatorio_incubacao.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("incubacao", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioEstoqueBaixoView(SensitiveReportView):
    template_name = "relatorios/relatorio_estoque_baixo.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("estoque_baixo"))
        return ctx


class RelatorioConsumoPeriodoView(SensitiveReportView):
    template_name = "relatorios/relatorio_consumo_periodo.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("consumo_periodo", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioConsumoLoteView(SensitiveReportView):
    template_name = "relatorios/relatorio_consumo_lote.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("consumo_lote", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioPerdasView(SensitiveReportView):
    template_name = "relatorios/relatorio_perdas.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("perdas", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioReproducaoView(SensitiveReportView):
    template_name = "relatorios/relatorio_reproducao.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("reproducao", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioConsumoCustoLoteView(SensitiveReportView):
    template_name = "relatorios/relatorio_consumo_custo_lote.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("consumo_custo_lote", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioPrevisaoEstoqueView(SensitiveReportView):
    template_name = "relatorios/relatorio_previsao_estoque.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("previsao_estoque", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioComparacaoLotesView(SensitiveReportView):
    template_name = "relatorios/relatorio_comparacao_lotes.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("comparacao_lotes", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioLucroLoteView(SensitiveReportView):
    template_name = "relatorios/relatorio_lucro_lote.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("lucro_lote", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioRankingLotesView(SensitiveReportView):
    template_name = "relatorios/relatorio_ranking_lotes.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("ranking_lotes", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


class RelatorioRankingReprodutoresView(SensitiveReportView):
    template_name = "relatorios/relatorio_ranking_reprodutores.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_report_context("ranking_reprodutores", self.request.GET.get("inicio"), self.request.GET.get("fim")))
        return ctx


def _pdf_table_data(report, data):
    if report == "lotes":
        return [
            ["Nome", "Codigo", "Finalidade", "Qtd", "Custo"],
            *[
                [l.nome, l.codigo, l.get_finalidade_display(), l.quantidade_atual or 0, f"R$ {l.custo_acumulado or 0}"]
                for l in data.get("lotes", [])
            ],
        ]
    if report == "aves":
        return [
            ["Codigo", "Nome", "Linhagem", "Finalidade", "Status"],
            *[
                [a.codigo_interno, a.nome, str(a.linhagem or "-"), a.get_finalidade_display(), a.get_status_display()]
                for a in data.get("aves", [])
            ],
        ]
    if report == "vacinas":
        return [
            ["Vacina", "Alvo", "Data", "Status"],
            *[
                [str(v.vacina), str(v.ave or v.lote or "-"), str(v.data_programada or "-"), v.get_status_display()]
                for v in data.get("vacinas", [])
            ],
        ]
    if report == "financeiro":
        return [
            ["Data", "Tipo", "Categoria", "Descricao", "Valor"],
            *[
                [str(l.data), l.get_tipo_display(), l.get_categoria_display(), l.descricao, f"R$ {l.valor or 0}"]
                for l in data.get("lancamentos", [])
            ],
        ]
    if report == "incubacao":
        return [
            ["Codigo", "Tipo", "Entrada", "Previsao", "Status"],
            *[
                [i.codigo, i.get_tipo_display(), str(i.data_entrada), str(i.previsao_eclosao or "-"), i.get_status_display()]
                for i in data.get("incubacoes", [])
            ],
        ]
    if report == "estoque_baixo":
        return [
            ["Item", "Categoria", "Qtd", "Minimo"],
            *[
                [i.nome, i.get_categoria_display(), f"{i.quantidade_atual or 0}", f"{i.estoque_minimo or 0}"]
                for i in data.get("itens", [])
            ],
        ]
    if report == "reproducao":
        return [
            ["Incubacao", "Lote", "Linhagem", "Ovos", "Nascidos", "Perdas", "Taxa"],
            *[
                [
                    i.codigo,
                    str(i.lote_relacionado or "-"),
                    str(
                        (i.matriz_responsavel.linhagem if i.matriz_responsavel and i.matriz_responsavel.linhagem else None)
                        or (i.lote_relacionado.linhagem_principal if i.lote_relacionado and i.lote_relacionado.linhagem_principal else "-")
                    ),
                    i.quantidade_ovos or 0,
                    i.quantidade_nascida or 0,
                    i.perdas or 0,
                    f"{i.taxa_eclosao or 0:.2f}%",
                ]
                for i in data.get("incubacoes", [])
            ],
        ]
    if report == "consumo_custo_lote":
        return [
            ["Lote", "Qtd", "Consumo", "Custo racao", "Custo sanitario", "Custo acumulado"],
            *[
                [
                    str(linha["lote"]),
                    linha["quantidade_atual"] or 0,
                    linha["consumo_racao_total"] or 0,
                    f"R$ {linha['custo_racao'] or 0}",
                    f"R$ {linha['custo_sanitario'] or 0}",
                    f"R$ {linha['custo_acumulado'] or 0}",
                ]
                for linha in data.get("linhas_lote", [])
            ],
        ]
    if report == "previsao_estoque":
        return [
            ["Item", "Qtd atual", "Consumo medio", "Duracao estimada", "Reposicao"],
            *[
                [
                    str(item["item"]),
                    item["item"].quantidade_atual or 0,
                    f"{item['consumo_medio'] or 0:.2f}",
                    f"{item['duracao_estimada']:.1f} dias" if item["duracao_estimada"] else "-",
                    "Proxima" if item["reposicao_proxima"] else "Normal",
                ]
                for item in data.get("itens_previsao", [])
            ],
        ]
    if report == "comparacao_lotes":
        return [
            ["Lote", "Qtd atual", "Custo", "Consumo", "Mortalidade", "Status rep.", "Lucro"],
            *[
                [
                    str(linha["lote"]),
                    linha["quantidade_atual"] or 0,
                    f"R$ {linha['custo_acumulado'] or 0}",
                    f"{linha['consumo_racao_total'] or 0}",
                    f"{linha['mortalidade_percentual'] or 0:.2f}%",
                    linha["status_reprodutivo_display"] or ("Nao reprodutivo" if not linha["reprodutivo"] else "-"),
                    f"R$ {linha['lucro_final'] or 0}",
                ]
                for linha in data.get("linhas_lote", [])
            ],
        ]
    if report == "lucro_lote":
        return [
            ["Lote", "Receita", "Custo racao", "Despesas extras", "Lucro final"],
            *[
                [
                    str(linha["lote"]),
                    f"R$ {linha['receita_vendas'] or 0}",
                    f"R$ {linha['custo_racao'] or 0}",
                    f"R$ {linha['despesas_extras'] or 0}",
                    f"R$ {linha['lucro_final'] or 0}",
                ]
                for linha in data.get("linhas_lote", [])
            ],
        ]
    if report == "ranking_lotes":
        return [
            ["Posicao", "Lote", "Lucro", "Mortalidade", "CA"],
            *[
                [
                    indice,
                    str(linha["lote"]),
                    f"R$ {linha['lucro_final'] or 0}",
                    f"{linha['mortalidade_percentual'] or 0:.2f}%",
                    f"{linha['conversao_alimentar'] or 0:.2f}",
                ]
                for indice, linha in enumerate(data.get("ranking_lotes", []), start=1)
            ],
        ]
    if report == "ranking_reprodutores":
        return [
            ["Posicao", "Ave", "Filhos", "Incubacoes", "Nascidos", "Eficiencia"],
            *[
                [
                    indice,
                    str(item["ave"]),
                    item["filhos"],
                    item["incubacoes"],
                    item["nascidos"],
                    f"{item['eficiencia'] or 0:.2f}",
                ]
                for indice, item in enumerate(data.get("ranking_reprodutores", []), start=1)
            ],
        ]
    return [["Relatorio"], [report]]


def _build_pdf_response_with_reportlab(report, data):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12,
    )
    meta = data.get("_pdf_meta", {})
    nome_granja = meta.get("nome_granja_pdf", "SISMGC")
    if meta.get("logo_pdf_path"):
        try:
            logo = Image(meta["logo_pdf_path"], width=2.2 * cm, height=2.2 * cm)
            story = [logo, Spacer(1, 0.15 * cm)]
        except Exception:
            story = []
    else:
        story = []
    story.extend(
        [
            Paragraph(nome_granja, subtitle_style),
            Paragraph(meta.get("titulo_relatorio", _report_label(report)), title_style),
            Paragraph(
                f"Gerado em {meta.get('gerado_em_pdf', datetime.now()).strftime('%d/%m/%Y %H:%M')} - Sistema SISMGC",
                subtitle_style,
            ),
        ]
    )
    if meta.get("filtros_pdf"):
        filtros = " | ".join(f"{rotulo}: {valor}" for rotulo, valor in meta["filtros_pdf"] if valor)
        story.append(Paragraph(f"Filtros usados: {filtros}", subtitle_style))
    if meta.get("resumo_pdf"):
        resumo_data = [[rotulo, str(valor)] for rotulo, valor in meta["resumo_pdf"]]
        resumo_table = Table(resumo_data, colWidths=[4.2 * cm, 5.3 * cm])
        resumo_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#bfdbfe")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbeafe")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.extend([Spacer(1, 0.12 * cm), resumo_table])
    story.append(Spacer(1, 0.28 * cm))
    table_data = _pdf_table_data(report, data)
    num_cols = len(table_data[0]) if table_data else 1
    available_width = landscape(A4)[0] - (doc.leftMargin + doc.rightMargin)
    col_width = available_width / max(num_cols, 1)
    table = Table(table_data, repeatRows=1, colWidths=[col_width] * num_cols)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#1e3a8a")),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        Paragraph(
            "Relatorio gerado automaticamente para acompanhamento operacional e gerencial.",
            ParagraphStyle(
                "ReportFooter",
                parent=styles["BodyText"],
                fontSize=8,
                leading=10,
                textColor=colors.HexColor("#64748b"),
            ),
        )
    )
    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="relatorio_{report}.pdf"'
    return response


class ExportRelatorioPDFView(SensitiveReportView):
    def get(self, request, *args, **kwargs):
        report = request.GET.get("report", "lotes")
        inicio_raw = request.GET.get("inicio")
        fim_raw = request.GET.get("fim")
        data = _report_context(report, inicio_raw, fim_raw)
        data["_pdf_meta"] = _build_report_meta(report, data, _parse_date(inicio_raw), _parse_date(fim_raw))
        try:
            from weasyprint import HTML
        except Exception:
            try:
                return _build_pdf_response_with_reportlab(report, data)
            except Exception:
                messages.error(
                    request,
                    "PDF indisponivel. WeasyPrint e fallback local nao puderam ser carregados neste ambiente.",
                )
                from django.shortcuts import redirect

                return redirect(request.META.get("HTTP_REFERER", "relatorios:index"))
        
        # Tenta usar template premium primeiro, fallback para template antigo
        template_names = [
            f"relatorios/relatorio_{report}_premium.html",  # Template novo premium
            "relatorios/print.html",  # Template antigo (fallback)
        ]
        
        try:
            html_string = render_to_string(template_names, {"report": report, **data})
        except Exception:
            # Se nenhum dos templates funcionar, usa o print.html antigo
            html_string = render_to_string("relatorios/print.html", {"report": report, **data})
        
        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename=relatorio_{report}.pdf"
        return response


class ExportRelatorioExcelView(SensitiveReportView):
    def get(self, request, *args, **kwargs):
        if openpyxl is None:
            return HttpResponse("openpyxl não está instalado.", status=500)
        report = request.GET.get("report", "lotes")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Relatorio"
        ws.append(["Relatório", report])
        data = _report_context(report, request.GET.get("inicio"), request.GET.get("fim"))
        if report == "lotes":
            ws.append(["Nome", "Código", "Finalidade", "Quantidade", "Custo"])
            for l in data.get("lotes", []):
                ws.append([l.nome, l.codigo, l.get_finalidade_display(), l.quantidade_atual, float(l.custo_acumulado)])
        elif report == "aves":
            ws.append(["Código", "Nome", "Linhagem", "Finalidade", "Status"])
            for a in data.get("aves", []):
                ws.append([a.codigo_interno, a.nome, str(a.linhagem), a.get_finalidade_display(), a.get_status_display()])
        elif report == "vacinas":
            ws.append(["Vacina", "Alvo", "Data", "Status"])
            for v in data.get("vacinas", []):
                alvo = v.ave or v.lote
                ws.append([str(v.vacina), str(alvo), v.data_programada.isoformat(), v.get_status_display()])
        elif report == "financeiro":
            ws.append(["Data", "Tipo", "Categoria", "Descrição", "Valor"])
            for l in data.get("lancamentos", []):
                ws.append([l.data.isoformat(), l.get_tipo_display(), l.get_categoria_display(), l.descricao, float(l.valor)])
        elif report == "incubacao":
            ws.append(["Código", "Tipo", "Entrada", "Previsão", "Status"])
            for i in data.get("incubacoes", []):
                ws.append([i.codigo, i.get_tipo_display(), i.data_entrada.isoformat(), str(i.previsao_eclosao), i.get_status_display()])
        elif report == "estoque_baixo":
            ws.append(["Item", "Categoria", "Qtd", "Mínimo"])
            for i in data.get("itens", []):
                ws.append([i.nome, i.get_categoria_display(), float(i.quantidade_atual), float(i.estoque_minimo)])
        elif report == "consumo_periodo":
            ws.append(["Data", "Item", "Quantidade", "Unidade"])
            for m in data.get("movimentos", []):
                ws.append([m.data.isoformat(), str(m.item), float(m.quantidade), m.item.unidade])
        elif report == "consumo_lote":
            ws.append(["Data", "Lote", "Item", "Quantidade", "Unidade"])
            for m in data.get("movimentos", []):
                ws.append([m.data.isoformat(), str(m.lote_relacionado), str(m.item), float(m.quantidade), m.item.unidade])
        elif report == "perdas":
            ws.append(["Data", "Item", "Quantidade", "Unidade", "Motivo"])
            for m in data.get("movimentos", []):
                ws.append([m.data.isoformat(), str(m.item), float(m.quantidade), m.item.unidade, m.get_motivo_display()])
        elif report == "reproducao":
            ws.append(["Incubação", "Lote", "Linhagem", "Ovos", "Nascidos", "Perdas", "Taxa eclosão"])
            for i in data.get("incubacoes", []):
                linhagem = ""
                if i.matriz_responsavel and i.matriz_responsavel.linhagem:
                    linhagem = str(i.matriz_responsavel.linhagem)
                elif i.lote_relacionado and i.lote_relacionado.linhagem_principal:
                    linhagem = str(i.lote_relacionado.linhagem_principal)
                ws.append([i.codigo, str(i.lote_relacionado), linhagem, i.quantidade_ovos, i.quantidade_nascida, i.perdas, float(i.taxa_eclosao)])
        elif report == "consumo_custo_lote":
            ws.append(["Lote", "Qtd", "Consumo ração", "Custo ração", "Custo sanitário", "Custo acumulado"])
            for linha in data.get("linhas_lote", []):
                ws.append([str(linha["lote"]), linha["quantidade_atual"] or 0, float(linha["consumo_racao_total"] or 0), float(linha["custo_racao"] or 0), float(linha["custo_sanitario"] or 0), float(linha["custo_acumulado"] or 0)])
        elif report == "previsao_estoque":
            ws.append(["Item", "Qtd atual", "Consumo médio", "Duração estimada"])
            for item in data.get("itens_previsao", []):
                ws.append([str(item["item"]), float(item["item"].quantidade_atual or 0), float(item["consumo_medio"] or 0), float(item["duracao_estimada"] or 0)])
        elif report == "comparacao_lotes":
            ws.append(["Lote", "Qtd", "Custo", "Consumo", "Mortalidade", "Reprodutivo"])
            for linha in data.get("linhas_lote", []):
                ws.append([str(linha["lote"]), linha["quantidade_atual"] or 0, float(linha["custo_acumulado"] or 0), float(linha["consumo_racao_total"] or 0), float(linha["mortalidade_percentual"] or 0), "Sim" if linha["reprodutivo"] else "Não"])
        elif report == "lucro_lote":
            ws.append(["Lote", "Receita", "Custo ração", "Despesas extras", "Lucro"])
            for linha in data.get("linhas_lote", []):
                ws.append([str(linha["lote"]), float(linha["receita_vendas"] or 0), float(linha["custo_racao"] or 0), float(linha["despesas_extras"] or 0), float(linha["lucro_final"] or 0)])
        elif report == "ranking_lotes":
            ws.append(["Lote", "Lucro", "Mortalidade", "CA"])
            for linha in data.get("ranking_lotes", []):
                ws.append([str(linha["lote"]), float(linha["lucro_final"] or 0), float(linha["mortalidade_percentual"] or 0), float(linha["conversao_alimentar"] or 0)])
        elif report == "ranking_reprodutores":
            ws.append(["Ave", "Filhos", "Incubações", "Nascidos", "Eficiência"])
            for item in data.get("ranking_reprodutores", []):
                ws.append([str(item["ave"]), item["filhos"], item["incubacoes"], item["nascidos"], float(item["eficiencia"] or 0)])
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f"attachment; filename=relatorio_{report}.xlsx"
        wb.save(response)
        return response

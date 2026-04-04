from datetime import date, timedelta
from django.db.models import Count, Q, Sum
from django.views.generic import TemplateView

from core.mixins import AuthenticatedView, user_has_role_or_perm
from core.services.alerts import get_alertas
from aves.models import Ave
from lotes.models import Lote
from estoque.models import ItemEstoque, MovimentoEstoque
from sanidade.models import AplicacaoVacina, Medicamento
from incubacao.models import Incubacao
from nascimentos.models import Nascimento
from vendas.models import Venda
from financeiro.models import LancamentoFinanceiro


class DashboardView(AuthenticatedView, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoje = date.today()
        mes_inicio = hoje.replace(day=1)
        alertas = get_alertas()
        can_view_vendas = user_has_role_or_perm(self.request.user, "vendas.view_venda")
        can_view_financeiro = user_has_role_or_perm(
            self.request.user,
            "financeiro.view_lancamentofinanceiro",
        )
        lotes_ativos_qs = Lote.objects.filter(status=Lote.STATUS_ATIVO)
        vacinas_pendentes_qs = AplicacaoVacina.objects.select_related("vacina").filter(
            status=AplicacaoVacina.STATUS_PENDENTE
        )
        incubacoes_andamento_qs = Incubacao.objects.filter(status=Incubacao.STATUS_EM_ANDAMENTO)
        nascimentos_recentes_qs = Nascimento.objects.select_related("lote_destino").filter(
            data__gte=hoje - timedelta(days=7)
        )
        contas_pendentes_qs = (
            Venda.objects.select_related("lote", "ave").filter(status_pagamento=Venda.STATUS_PENDENTE)
            if can_view_vendas
            else Venda.objects.none()
        )
        financeiro_totais = (
            LancamentoFinanceiro.objects.aggregate(
                entradas=Sum("valor", filter=Q(tipo=LancamentoFinanceiro.TIPO_ENTRADA)),
                saidas=Sum("valor", filter=Q(tipo=LancamentoFinanceiro.TIPO_SAIDA)),
                saidas_mes=Sum(
                    "valor",
                    filter=Q(tipo=LancamentoFinanceiro.TIPO_SAIDA, data__gte=mes_inicio),
                ),
                entradas_mes=Sum(
                    "valor",
                    filter=Q(tipo=LancamentoFinanceiro.TIPO_ENTRADA, data__gte=mes_inicio),
                ),
            )
            if can_view_financeiro
            else {"entradas": 0, "saidas": 0, "saidas_mes": 0, "entradas_mes": 0}
        )

        ctx["total_aves"] = Ave.objects.count()
        ctx["lotes_ativos"] = lotes_ativos_qs.count()
        ctx["aves_por_finalidade"] = (
            Ave.objects.values("finalidade").annotate(total=Count("id")).order_by()
        )
        ctx["estoque_baixo"] = alertas["estoque_baixo"][:5]
        ctx["vacinas_pendentes"] = vacinas_pendentes_qs[:5]
        ctx["medicamentos_vencendo"] = alertas["medicamentos_vencendo"][:5]
        ctx["janela_dias"] = alertas["janela_dias"]
        ctx["estoque_baixo_count"] = len(alertas["estoque_baixo"])
        ctx["medicamentos_vencendo_count"] = len(alertas["medicamentos_vencendo"])
        ctx["incubacoes_proximas_count"] = len(alertas["incubacoes_proximas"])
        ctx["nascimentos_previstos_count"] = len(alertas["nascimentos_previstos"])
        ctx["carencias_ativas_count"] = len(alertas["carencias_ativas"])
        ctx["vacinas_pendentes_count"] = vacinas_pendentes_qs.count()
        ctx["incubacoes_andamento"] = incubacoes_andamento_qs[:5]
        ctx["nascimentos_recentes"] = nascimentos_recentes_qs[:5]
        ctx["incubacoes_proximas"] = alertas["incubacoes_proximas"][:5]
        ctx["nascimentos_previstos"] = alertas["nascimentos_previstos"][:5]
        ctx["carencias_ativas"] = alertas["carencias_ativas"][:5]
        ctx["incubacoes_andamento_count"] = incubacoes_andamento_qs.count()
        ctx["nascimentos_recentes_count"] = nascimentos_recentes_qs.count()
        ctx["vendas_recentes"] = (
            Venda.objects.select_related("lote", "ave").order_by("-data")[:5]
            if can_view_vendas
            else []
        )
        ctx["despesas_recentes"] = (
            LancamentoFinanceiro.objects.select_related("lote", "ave")
            .filter(tipo=LancamentoFinanceiro.TIPO_SAIDA)
            .order_by("-data")[:5]
            if can_view_financeiro
            else []
        )
        ctx["saldo_atual"] = (financeiro_totais["entradas"] or 0) - (financeiro_totais["saidas"] or 0)
        ctx["lucro_mes"] = (financeiro_totais["entradas_mes"] or 0) - (financeiro_totais["saidas_mes"] or 0)
        ctx["total_vendas_mes"] = (
            Venda.objects.filter(data__gte=mes_inicio).aggregate(total=Sum("valor_total"))["total"] or 0
            if can_view_vendas
            else 0
        )
        ctx["total_gastos_mes"] = financeiro_totais["saidas_mes"] or 0
        ctx["lote_maior_custo"] = Lote.objects.order_by("-custo_acumulado").first()
        ctx["lote_pior_conversao"] = Lote.objects.order_by("-consumo_acumulado").first()
        ctx["lote_maior_custo_valor"] = ctx["lote_maior_custo"].custo_acumulado if ctx["lote_maior_custo"] else 0
        ctx["lote_pior_conversao_valor"] = (
            ctx["lote_pior_conversao"].conversao_alimentar if ctx["lote_pior_conversao"] else 0
        )
        lotes_problema = []
        for lote in lotes_ativos_qs[:50]:
            problemas = []
            if lote.mortalidade_percentual >= 10:
                problemas.append("mortalidade alta")
            if lote.reprodutivo and lote.status_reprodutivo == Lote.REPRO_STATUS_PAUSADO:
                problemas.append("reprodução pausada")
            if problemas:
                lotes_problema.append({"lote": lote, "problemas": ", ".join(problemas)})
        contas_pendentes = contas_pendentes_qs.order_by("-data")[:5]
        eventos_importantes = sorted(
            [
                {
                    "tipo": "Eclosão",
                    "data": inc.previsao_eclosao,
                    "descricao": f"{inc.codigo} com eclosão prevista",
                }
                for inc in alertas["incubacoes_proximas"][:5]
                if inc.previsao_eclosao
            ]
            + [
                {
                    "tipo": "Nascimento previsto",
                    "data": inc.previsao_eclosao,
                    "descricao": f"{inc.codigo} pode gerar nascimento",
                }
                for inc in alertas["nascimentos_previstos"][:5]
                if inc.previsao_eclosao
            ],
            key=lambda item: item["data"] or hoje,
        )[:6]
        ctx["contas_pendentes"] = contas_pendentes
        ctx["contas_pendentes_count"] = contas_pendentes_qs.count()
        ctx["lotes_problema"] = lotes_problema[:5]
        ctx["lotes_problema_count"] = len(lotes_problema)
        ctx["eventos_importantes"] = eventos_importantes
        ctx["eventos_importantes_count"] = len(eventos_importantes)
        ctx["can_view_vendas"] = can_view_vendas
        ctx["can_view_financeiro"] = can_view_financeiro
        # Gráficos simples - sumarização
        ctx["graf_consumo_racao"] = (
            MovimentoEstoque.objects.filter(item__categoria=ItemEstoque.CAT_RACAO)
            .values("data__month")
            .annotate(total=Sum("quantidade"))
            .order_by()
        )
        ctx["graf_despesas_categoria"] = (
            LancamentoFinanceiro.objects.filter(tipo=LancamentoFinanceiro.TIPO_SAIDA)
            .values("categoria")
            .annotate(total=Sum("valor"))
            .order_by()
            if can_view_financeiro
            else []
        )
        ctx["graf_vendas_periodo"] = (
            Venda.objects.values("data__month").annotate(total=Sum("valor_total")).order_by()
            if can_view_vendas
            else []
        )
        ctx["graf_nascimentos_periodo"] = (
            Nascimento.objects.values("data__month").annotate(total=Sum("quantidade_nascida")).order_by()
        )
        return ctx

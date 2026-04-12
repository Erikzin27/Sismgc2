from datetime import date, timedelta
from django.db.models import Count, Q, Sum
from django.views.generic import TemplateView
from django.core.cache import cache

from core.mixins import AuthenticatedView, user_has_role_or_perm
from core.services.alerts import get_alertas
from core.services.insights import gerar_sugestoes
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

    def _get_cache_key(self, user, suffix):
        role = getattr(user, "role", "anon")
        return f"sismgc:dashboard:{role}:{suffix}"

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true" and self.request.GET.get("partial") == "alerts":
            return ["dashboard/_alerts.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoje = date.today()
        mes_inicio = hoje.replace(day=1)
        alertas = get_alertas(self.request.user)
        can_view_vendas = user_has_role_or_perm(self.request.user, "vendas.view_venda")
        can_view_financeiro = user_has_role_or_perm(
            self.request.user,
            "financeiro.view_lancamentofinanceiro",
        )
        can_view_sanidade = user_has_role_or_perm(
            self.request.user,
            ["sanidade.view_vacina", "sanidade.view_tratamento"],
        )
        can_view_incubacao = user_has_role_or_perm(self.request.user, "incubacao.view_incubacao")
        lotes_ativos_qs = Lote.objects.filter(status=Lote.STATUS_ATIVO).only(
            "id",
            "nome",
            "codigo",
            "quantidade_inicial",
            "quantidade_atual",
            "custo_acumulado",
            "consumo_acumulado",
            "reprodutivo",
            "status_reprodutivo",
        )
        vacinas_pendentes_qs = (
            AplicacaoVacina.objects.select_related("vacina").filter(
                status=AplicacaoVacina.STATUS_PENDENTE
            )
            if can_view_sanidade
            else AplicacaoVacina.objects.none()
        )
        vacinas_atrasadas_qs = vacinas_pendentes_qs.filter(data_programada__lt=hoje)
        vacinas_urgencia_critica_qs = vacinas_pendentes_qs.filter(data_programada__lt=hoje - timedelta(days=6))
        vacinas_urgencia_alta_qs = vacinas_pendentes_qs.filter(
            data_programada__lt=hoje - timedelta(days=2),
            data_programada__gte=hoje - timedelta(days=6),
        )
        incubacoes_andamento_qs = (
            Incubacao.objects.filter(status=Incubacao.STATUS_EM_ANDAMENTO)
            if can_view_incubacao
            else Incubacao.objects.none()
        )
        nascimentos_recentes_qs = Nascimento.objects.select_related("lote_destino").filter(
            data__gte=hoje - timedelta(days=7)
        )
        contas_pendentes_qs = (
            Venda.objects.select_related("lote", "ave").filter(status_pagamento=Venda.STATUS_PENDENTE)
            if can_view_vendas
            else Venda.objects.none()
        )
        snapshot_key = self._get_cache_key(self.request.user, "snapshot")
        snapshot = cache.get(snapshot_key)
        if snapshot is None:
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
            saldo_atual = (financeiro_totais["entradas"] or 0) - (financeiro_totais["saidas"] or 0)
            lucro_mes = (financeiro_totais["entradas_mes"] or 0) - (financeiro_totais["saidas_mes"] or 0)
            total_vendas_mes = (
                Venda.objects.filter(data__gte=mes_inicio).aggregate(total=Sum("valor_total"))["total"] or 0
                if can_view_vendas
                else 0
            )
            total_gastos_mes = financeiro_totais["saidas_mes"] or 0
            resumo_financeiro_hoje = (
                LancamentoFinanceiro.objects.filter(data=hoje).aggregate(
                    entradas=Sum("valor", filter=Q(tipo=LancamentoFinanceiro.TIPO_ENTRADA)),
                    saidas=Sum("valor", filter=Q(tipo=LancamentoFinanceiro.TIPO_SAIDA)),
                )
                if can_view_financeiro
                else {"entradas": 0, "saidas": 0}
            )
            resumo_financeiro_hoje["saldo"] = (
                (resumo_financeiro_hoje.get("entradas") or 0)
                - (resumo_financeiro_hoje.get("saidas") or 0)
            )
            if can_view_financeiro:
                meses = []
                ano = hoje.year
                mes = hoje.month
                for _ in range(6):
                    meses.append((ano, mes))
                    mes -= 1
                    if mes == 0:
                        mes = 12
                        ano -= 1
                meses.reverse()
                labels = [f"{m:02d}/{a}" for a, m in meses]
                entradas_series = []
                saidas_series = []
                for a, m in meses:
                    entradas_series.append(
                        LancamentoFinanceiro.objects.filter(
                            tipo=LancamentoFinanceiro.TIPO_ENTRADA, data__year=a, data__month=m
                        ).aggregate(total=Sum("valor"))["total"]
                        or 0
                    )
                    saidas_series.append(
                        LancamentoFinanceiro.objects.filter(
                            tipo=LancamentoFinanceiro.TIPO_SAIDA, data__year=a, data__month=m
                        ).aggregate(total=Sum("valor"))["total"]
                        or 0
                    )
                financeiro_chart = {"labels": labels, "entradas": entradas_series, "saidas": saidas_series}
            else:
                financeiro_chart = {"labels": [], "entradas": [], "saidas": []}

            snapshot = {
                "financeiro_totais": financeiro_totais,
                "saldo_atual": saldo_atual,
                "lucro_mes": lucro_mes,
                "total_vendas_mes": total_vendas_mes,
                "total_gastos_mes": total_gastos_mes,
                "resumo_financeiro_hoje": resumo_financeiro_hoje,
                "financeiro_chart": financeiro_chart,
            }
            cache.set(snapshot_key, snapshot, 60)
        financeiro_totais = snapshot["financeiro_totais"]

        ctx["total_aves"] = Ave.objects.count()
        ctx["lotes_ativos"] = lotes_ativos_qs.count()
        ctx["aves_por_finalidade"] = (
            Ave.objects.values("finalidade").annotate(total=Count("id")).order_by()
        )
        ctx["estoque_baixo"] = alertas["estoque_baixo"][:5]
        ctx["vacinas_pendentes"] = vacinas_pendentes_qs[:5]
        ctx["medicamentos_vencendo"] = alertas["medicamentos_vencendo"][:5]
        ctx["estoque_critico"] = alertas.get("estoque_critico", [])[:5]
        ctx["janela_dias"] = alertas["janela_dias"]
        ctx["estoque_baixo_count"] = len(alertas["estoque_baixo"])
        ctx["estoque_critico_count"] = len(alertas.get("estoque_critico", []))
        ctx["medicamentos_vencendo_count"] = len(alertas["medicamentos_vencendo"])
        ctx["itens_vencidos_count"] = alertas.get("itens_vencidos", []).count() if alertas.get("itens_vencidos") is not None else 0
        ctx["incubacoes_proximas_count"] = len(alertas["incubacoes_proximas"])
        ctx["nascimentos_previstos_count"] = len(alertas["nascimentos_previstos"])
        ctx["carencias_ativas_count"] = len(alertas["carencias_ativas"])
        ctx["vacinas_pendentes_count"] = vacinas_pendentes_qs.count()
        ctx["vacinas_atrasadas_count"] = alertas.get("vacinas_atrasadas", []).count() if alertas.get("vacinas_atrasadas") is not None else 0
        ctx["contas_vencidas_count"] = alertas.get("contas_vencidas", []).count() if alertas.get("contas_vencidas") is not None else 0
        ctx["contas_proximas_count"] = alertas.get("contas_proximas", []).count() if alertas.get("contas_proximas") is not None else 0
        ctx["vacinas_atrasadas_count"] = vacinas_atrasadas_qs.count()
        ctx["vacinas_urgencia_critica_count"] = vacinas_urgencia_critica_qs.count()
        ctx["vacinas_urgencia_alta_count"] = vacinas_urgencia_alta_qs.count()
        ctx["incubacoes_andamento"] = incubacoes_andamento_qs[:5]
        ctx["nascimentos_recentes"] = nascimentos_recentes_qs[:5]
        ctx["incubacoes_proximas"] = alertas["incubacoes_proximas"][:5]
        ctx["nascimentos_previstos"] = alertas["nascimentos_previstos"][:5]
        ctx["carencias_ativas"] = alertas["carencias_ativas"][:5]
        ctx["sugestoes"] = gerar_sugestoes(alertas)
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
        ctx["saldo_atual"] = snapshot["saldo_atual"]
        ctx["lucro_mes"] = snapshot["lucro_mes"]
        ctx["entradas_mes"] = financeiro_totais["entradas_mes"] or 0
        ctx["saidas_mes"] = financeiro_totais["saidas_mes"] or 0
        ctx["total_vendas_mes"] = snapshot["total_vendas_mes"]
        ctx["total_gastos_mes"] = snapshot["total_gastos_mes"]
        ctx["lote_maior_custo"] = Lote.objects.order_by("-custo_acumulado").first()
        ctx["lote_pior_conversao"] = Lote.objects.order_by("-consumo_acumulado").first()
        ctx["lote_maior_custo_valor"] = ctx["lote_maior_custo"].custo_acumulado if ctx["lote_maior_custo"] else 0
        ctx["lote_pior_conversao_valor"] = (
            ctx["lote_pior_conversao"].conversao_alimentar if ctx["lote_pior_conversao"] else 0
        )
        def _conversao_simples(lote):
            if lote.quantidade_inicial and lote.consumo_acumulado:
                return float(lote.consumo_acumulado) / max(float(lote.quantidade_inicial), 1)
            return 0

        ranking_key = self._get_cache_key(self.request.user, "ranking_lotes")
        ranking_ids = cache.get(ranking_key)
        if ranking_ids:
            lote_map = {
                lote.id: lote
                for lote in Lote.objects.filter(id__in=ranking_ids).only(
                    "id",
                    "nome",
                    "codigo",
                    "quantidade_inicial",
                    "quantidade_atual",
                    "custo_acumulado",
                    "consumo_acumulado",
                )
            }
            ranking_lotes = [lote_map[lid] for lid in ranking_ids if lid in lote_map]
        else:
            ranking_lotes = sorted(
                list(lotes_ativos_qs[:30]),
                key=lambda lote: (
                    float(lote.mortalidade_percentual or 0),
                    _conversao_simples(lote),
                    float(lote.custo_acumulado or 0),
                ),
            )
            ranking_ids = [lote.id for lote in ranking_lotes[:10]]
            cache.set(ranking_key, ranking_ids, 30)
        ctx["ranking_lotes_dashboard"] = ranking_lotes[:5]
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
        ctx["resumo_financeiro_hoje"] = snapshot["resumo_financeiro_hoje"]
        ctx["financeiro_chart"] = snapshot["financeiro_chart"]
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

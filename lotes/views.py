from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Avg, Count, Exists, OuterRef, Q
from django.utils import timezone

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin, user_has_role_or_perm
from .models import Lote
from linhagens.models import Linhagem
from historico.models import HistoricoEvento
from .forms import LoteForm
from sanidade.models import AplicacaoVacina, Tratamento
from incubacao.models import Incubacao


class LoteListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Lote
    template_name = "lotes/lote_list.html"
    context_object_name = "lotes"
    paginate_by = 20
    permission_required = "lotes.view_lote"
    search_fields = ["nome", "codigo", "local"]
    filter_fields = ["finalidade", "status", "linhagem_principal"]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("linhagem_principal")
            .prefetch_related(
                "vacinas__vacina",
                "tratamentos__medicamento",
                "vendas",
                "abates",
            )
            .only(
                "id", "codigo", "nome", "local", "finalidade", "status", 
                "quantidade_atual", "custo_acumulado", "data_criacao",
                "linhagem_principal__id", "linhagem_principal__nome"
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["comparativo"] = Lote.objects.aggregate(
            media_quantidade=Avg("quantidade_atual"),
            media_custo=Avg("custo_acumulado"),
        )
        hoje = timezone.localdate()
        page_lotes = ctx.get("lotes")
        lote_ids = [l.pk for l in page_lotes] if page_lotes else []
        can_view_sanidade = user_has_role_or_perm(
            user,
            ["sanidade.view_vacina", "sanidade.view_tratamento"],
        )
        
        # Single query para todos os mapas usando annotate
        vacinas_atrasadas_map = {}
        carencias_ativas_map = {}
        incubacoes_atrasadas_map = {}
        
        if lote_ids:
            # Query única para vacinas atrasadas por lote
            vacinas_atrasadas = (
                AplicacaoVacina.objects
                .filter(
                    status=AplicacaoVacina.STATUS_PENDENTE,
                    data_programada__lt=hoje,
                    lote__isnull=False,
                    lote_id__in=lote_ids,
                )
                .values("lote_id")
                .annotate(total=Count("id"))
            )
            vacinas_atrasadas_map = {row["lote_id"]: row["total"] for row in vacinas_atrasadas}
            
            # Query única para carências usando prefetch
            if can_view_sanidade:
                aplicacoes = (
                    AplicacaoVacina.objects
                    .select_related("vacina")
                    .filter(
                        status=AplicacaoVacina.STATUS_APLICADA,
                        data_aplicacao__isnull=False,
                        lote__isnull=False,
                        lote_id__in=lote_ids,
                        vacina__carencia_dias__gt=0,
                    )
                )
                carencias_map = {}
                for app in aplicacoes:
                    if app.carencia_ativa and app.lote_id:
                        carencias_map[app.lote_id] = carencias_map.get(app.lote_id, 0) + 1
                
                # Query única para tratamentos com carência
                tratamentos = (
                    Tratamento.objects
                    .filter(
                        data_fim__isnull=False,
                        periodo_carencia__gt=0,
                        lote__isnull=False,
                        lote_id__in=lote_ids,
                    )
                )
                for trat in tratamentos:
                    if trat.carencia_ativa and trat.lote_id:
                        carencias_map[trat.lote_id] = carencias_map.get(trat.lote_id, 0) + 1
                carencias_ativas_map = carencias_map

            # Query única para incubações atrasadas
            incubacoes_atrasadas = (
                Incubacao.objects
                .filter(
                    status=Incubacao.STATUS_EM_ANDAMENTO,
                    previsao_eclosao__isnull=False,
                    previsao_eclosao__lt=hoje,
                    lote_relacionado__isnull=False,
                    lote_relacionado_id__in=lote_ids,
                )
                .values("lote_relacionado_id")
                .annotate(total=Count("id"))
            )
            incubacoes_atrasadas_map = {row["lote_relacionado_id"]: row["total"] for row in incubacoes_atrasadas}

        ctx["vacinas_atrasadas_map"] = vacinas_atrasadas_map
        ctx["carencias_ativas_map"] = carencias_ativas_map
        ctx["incubacoes_atrasadas_map"] = incubacoes_atrasadas_map
        
        # Cache linhagens apenas se não for AJAX
        if self.request.headers.get("HX-Request") != "true":
            ctx["linhagens_filtro"] = (
                Linhagem.objects
                .filter(lotes__isnull=False)
                .distinct()
                .only("id", "nome")
                .order_by("nome")
            )
        
        return ctx


class LoteDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = Lote
    template_name = "lotes/lote_detail.html"
    context_object_name = "lote"
    permission_required = "lotes.view_lote"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("linhagem_principal")
            .prefetch_related(
                "aves",
                "vendas",
                "abates",
                "incubacoes",
                "nascimentos",
                "vacinas__vacina",
                "tratamentos__medicamento",
                "movimentoestoque_set__item",
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lote = self.object
        user = self.request.user
        can_view_historico = bool(user and user.is_authenticated and user.is_manager)
        can_view_sanidade = user_has_role_or_perm(
            user,
            ["sanidade.view_vacina", "sanidade.view_tratamento"],
        )
        can_view_vendas = user_has_role_or_perm(user, "vendas.view_venda")
        can_view_abates = user_has_role_or_perm(user, "abate.view_abate")
        can_view_incubacao = user_has_role_or_perm(user, "incubacao.view_incubacao")
        can_view_movimentos = user_has_role_or_perm(user, "estoque.view_movimentoestoque")
        aves = list(lote.aves.all())
        vacinas = list(lote.vacinas.all())
        tratamentos = list(lote.tratamentos.all())
        vendas = list(lote.vendas.all())
        abates = list(lote.abates.all())
        incubacoes = list(lote.incubacoes.all())
        nascimentos = list(lote.nascimentos.all())
        movimentos = list(lote.movimentoestoque_set.all()) if hasattr(lote, "movimentoestoque_set") else []
        ctx["vacinas"] = vacinas if can_view_sanidade else []
        ctx["tratamentos"] = tratamentos if can_view_sanidade else []
        ctx["vendas"] = vendas if can_view_vendas else []
        ctx["abates"] = abates if can_view_abates else []
        ctx["incubacoes"] = incubacoes if can_view_incubacao else []
        ctx["nascimentos"] = nascimentos
        ctx["movimentos"] = movimentos if can_view_movimentos else []
        ctx["historico"] = (
            HistoricoEvento.objects.filter(entidade="Lote", referencia_id=lote.pk)[:50]
            if can_view_historico
            else []
        )

        consumo_racao = sum(
            (mov.quantidade or 0)
            for mov in movimentos
            if mov.tipo == "saida" and getattr(mov.item, "categoria", None) == "racao"
        )
        # Mini série de consumo/custo por mês (últimos 6 meses)
        meses_ref = []
        ano = timezone.localdate().year
        mes = timezone.localdate().month
        for _ in range(6):
            meses_ref.append((ano, mes))
            mes -= 1
            if mes == 0:
                mes = 12
                ano -= 1
        meses_ref.reverse()
        consumo_por_mes = {f"{a:04d}-{m:02d}": 0 for a, m in meses_ref}
        custo_por_mes = {f"{a:04d}-{m:02d}": 0 for a, m in meses_ref}
        for mov in movimentos:
            if mov.tipo != "saida":
                continue
            if getattr(mov.item, "categoria", None) != "racao":
                continue
            if not mov.data:
                continue
            chave = f"{mov.data.year:04d}-{mov.data.month:02d}"
            if chave in consumo_por_mes:
                consumo_por_mes[chave] += float(mov.quantidade or 0)
                custo_por_mes[chave] += float(mov.quantidade or 0) * float(mov.custo_unitario or 0)
        labels = [f"{m:02d}/{a}" for a, m in meses_ref]
        consumo_series = [round(consumo_por_mes[f"{a:04d}-{m:02d}"], 2) for a, m in meses_ref]
        custo_series = [round(custo_por_mes[f"{a:04d}-{m:02d}"], 2) for a, m in meses_ref]
        dias_desde_inicio = 0
        if lote.data_criacao:
            try:
                dias_desde_inicio = max((timezone.localdate() - lote.data_criacao).days, 1)
            except Exception:
                dias_desde_inicio = 0
        consumo_medio_dia = (consumo_racao / dias_desde_inicio) if dias_desde_inicio else 0
        consumo_por_ave = consumo_racao / max(lote.quantidade_atual or 0, 1)
        total_incubacoes = len(incubacoes) if can_view_incubacao else 0
        total_ovos = sum((inc.quantidade_ovos or 0) for inc in incubacoes) if can_view_incubacao else 0
        total_nascidos = sum((nasc.quantidade_nascida or 0) for nasc in nascimentos)
        taxa_eclosao = (total_nascidos / total_ovos * 100) if total_ovos else 0

        ctx["resumo"] = {
            "mortalidade": lote.mortalidade_percentual,
            "consumo_racao": consumo_racao,
            "conversao": lote.conversao_alimentar,
        }
        ctx["resumo_reproducao"] = {
            "total_incubacoes": total_incubacoes,
            "total_ovos": total_ovos,
            "total_nascidos": total_nascidos,
            "taxa_eclosao": taxa_eclosao,
        }
        vacinas_pendentes = sum(1 for vac in vacinas if vac.status == "pendente")
        vacinas_atrasadas = sum(1 for vac in vacinas if getattr(vac, "atrasada", False))
        tratamentos_ativos = sum(1 for trat in tratamentos if getattr(trat, "em_andamento", False))
        carencias_ativas = []
        if can_view_sanidade:
            for vac in vacinas:
                if vac.carencia_ativa:
                    carencias_ativas.append(vac)
            for trat in tratamentos:
                if trat.carencia_ativa:
                    carencias_ativas.append(trat)

        ctx["painel_operacional"] = {
            "aves": len(aves),
            "vacinas_pendentes": vacinas_pendentes,
            "vacinas_atrasadas": vacinas_atrasadas,
            "tratamentos_ativos": tratamentos_ativos,
            "movimentos": len(movimentos),
            "nascimentos": len(nascimentos),
            "incubacoes": total_incubacoes,
        }
        ctx["painel_inteligente"] = {
            "consumo_total": consumo_racao,
            "consumo_medio_dia": consumo_medio_dia,
            "consumo_por_ave": consumo_por_ave,
            "custo_racao": lote.custo_racao,
            "custo_sanitario": lote.custo_sanitario,
            "despesas_extras": lote.despesas_extras,
            "vacinas_pendentes": vacinas_pendentes,
            "vacinas_atrasadas": vacinas_atrasadas,
            "tratamentos_ativos": tratamentos_ativos,
            "carencias_ativas": len(carencias_ativas),
            "taxa_eclosao": taxa_eclosao,
        }
        ctx["lote_consumo_chart"] = {
            "labels": labels,
            "consumo": consumo_series,
            "custo": custo_series,
        }
        proximas_vacinas = sorted(
            [vac for vac in vacinas if getattr(vac, "status", "") == "pendente" and vac.data_programada],
            key=lambda vac: vac.data_programada,
        )
        proximas_incubacoes = sorted(
            [inc for inc in incubacoes if getattr(inc, "previsao_eclosao", None)],
            key=lambda inc: inc.previsao_eclosao,
        )
        alertas_lote = []
        if lote.mortalidade_percentual >= 10:
            alertas_lote.append(
                {
                    "tipo": "Mortalidade",
                    "descricao": f"Mortalidade em {lote.mortalidade_percentual:.2f}% exige revisão do manejo.",
                    "nivel": "danger",
                }
            )
        if consumo_racao and lote.quantidade_atual:
            if consumo_por_ave > 5:
                alertas_lote.append(
                    {
                        "tipo": "Consumo",
                        "descricao": f"Consumo médio por ave em {consumo_por_ave:.2f} kg no lote.",
                        "nivel": "warning",
                    }
                )
        if lote.reprodutivo and lote.status_reprodutivo == Lote.REPRO_STATUS_PAUSADO:
            alertas_lote.append(
                {
                    "tipo": "Reprodução",
                    "descricao": "Lote reprodutivo está com o status pausado.",
                    "nivel": "warning",
                }
            )
        if lote.reprodutivo and total_ovos and taxa_eclosao < 70:
            alertas_lote.append(
                {
                    "tipo": "Eclosão",
                    "descricao": f"Taxa de eclosão em {taxa_eclosao:.1f}% abaixo do esperado.",
                    "nivel": "warning",
                }
            )
        if vacinas_atrasadas:
            alertas_lote.append(
                {
                    "tipo": "Vacinação",
                    "descricao": f"{vacinas_atrasadas} vacina(s) em atraso para este lote.",
                    "nivel": "danger",
                }
            )
        if tratamentos_ativos:
            alertas_lote.append(
                {
                    "tipo": "Sanidade",
                    "descricao": f"{tratamentos_ativos} tratamento(s) em andamento.",
                    "nivel": "info",
                }
            )
        if can_view_sanidade and carencias_ativas:
            alertas_lote.append(
                {
                    "tipo": "Carência",
                    "descricao": f"{len(carencias_ativas)} carência(s) sanitária(s) ativa(s).",
                    "nivel": "warning",
                }
            )
        if proximas_vacinas:
            alertas_lote.append(
                {
                    "tipo": "Vacinação",
                    "descricao": f"Próxima vacina prevista em {proximas_vacinas[0].data_programada}.",
                    "nivel": "info",
                }
            )
        if proximas_incubacoes and can_view_incubacao:
            alertas_lote.append(
                {
                    "tipo": "Eclosão",
                    "descricao": f"Próxima eclosão prevista em {proximas_incubacoes[0].previsao_eclosao}.",
                    "nivel": "info",
                }
            )
        ctx["alertas_lote"] = alertas_lote
        ctx["atalhos_lote"] = {
            "vacinacao": can_view_sanidade,
            "tratamentos": can_view_sanidade,
            "incubacao": can_view_incubacao,
            "vendas": can_view_vendas,
            "movimentos": can_view_movimentos,
        }
        carencias = []
        if can_view_sanidade:
            for vac in vacinas:
                if vac.carencia_ativa:
                    carencias.append(
                        {
                            "data": vac.data_final_carencia,
                            "tipo": "Vacina",
                            "descricao": f"{vac.vacina} até {vac.data_final_carencia}",
                        }
                    )
            for trat in tratamentos:
                if trat.carencia_ativa:
                    carencias.append(
                        {
                            "data": trat.data_final_carencia,
                            "tipo": "Tratamento",
                            "descricao": f"{trat.doenca} até {trat.data_final_carencia}",
                        }
                    )
        ctx["carencias_ativas"] = sorted(carencias, key=lambda item: item["data"])[:10]
        timeline = []
        timeline.append(
            {
                "data": lote.data_criacao,
                "tipo": "Criação",
                "descricao": f"Lote cadastrado com finalidade {lote.get_finalidade_display()}",
            }
        )
        if lote.reprodutivo and lote.data_inicio_reproducao:
            timeline.append(
                {
                    "data": lote.data_inicio_reproducao,
                    "tipo": "Reprodução",
                    "descricao": f"Início reprodutivo ({lote.get_status_reprodutivo_display() or 'sem status'})",
                }
            )
        if can_view_movimentos:
            for mov in movimentos[:20]:
                timeline.append(
                    {
                        "data": mov.data,
                        "tipo": "Movimentação",
                        "descricao": f"{mov.get_tipo_display()} - {mov.item}",
                    }
                )
        if can_view_sanidade:
            for vac in vacinas[:20]:
                timeline.append(
                    {
                        "data": vac.data_aplicacao or vac.data_programada,
                        "tipo": "Vacina",
                        "descricao": f"{vac.vacina} ({vac.get_status_display()})",
                    }
                )
            for trat in tratamentos[:20]:
                timeline.append(
                    {
                        "data": trat.data_inicio,
                        "tipo": "Tratamento",
                        "descricao": f"{trat.doenca} - {trat.medicamento}",
                    }
                )
        if can_view_incubacao:
            for inc in incubacoes[:20]:
                timeline.append(
                    {
                        "data": inc.data_entrada,
                        "tipo": "Incubação",
                        "descricao": f"{inc.codigo} - {inc.quantidade_ovos} ovos",
                    }
                )
        for nasc in nascimentos[:20]:
            timeline.append(
                {
                    "data": nasc.data,
                    "tipo": "Nascimento",
                    "descricao": f"{nasc.quantidade_nascida} aves nascidas",
                }
            )
        if can_view_vendas:
            for venda in vendas[:20]:
                timeline.append(
                    {
                        "data": venda.data,
                        "tipo": "Venda",
                        "descricao": f"{venda.produto} - {venda.cliente}",
                    }
                )
        if can_view_abates:
            for abate in abates[:20]:
                timeline.append(
                    {
                        "data": abate.data,
                        "tipo": "Abate",
                        "descricao": f"{abate.quantidade_abatida} aves abatidas",
                    }
                )
        if can_view_historico:
            for hist in ctx["historico"]:
                timeline.append(
                    {
                        "data": hist.created_at.date(),
                        "tipo": hist.get_acao_display(),
                        "descricao": hist.descricao,
                    }
                )
        ctx["timeline_lote"] = sorted(
            [item for item in timeline if item.get("data")],
            key=lambda item: item["data"],
            reverse=True,
        )[:50]
        ctx["can_view_historico"] = can_view_historico
        ctx["can_view_sanidade"] = can_view_sanidade
        ctx["can_view_vendas"] = can_view_vendas
        ctx["can_view_abates"] = can_view_abates
        ctx["can_view_incubacao"] = can_view_incubacao
        ctx["can_view_movimentos"] = can_view_movimentos
        return ctx


class LoteCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = Lote
    form_class = LoteForm
    template_name = "lotes/lote_form.html"
    success_url = reverse_lazy("lotes:list")
    permission_required = "lotes.add_lote"


class LoteUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = Lote
    form_class = LoteForm
    template_name = "lotes/lote_form.html"
    success_url = reverse_lazy("lotes:list")
    permission_required = "lotes.change_lote"


class LoteDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = Lote
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("lotes:list")
    permission_required = "lotes.delete_lote"

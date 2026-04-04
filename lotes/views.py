from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Avg

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin, user_has_role_or_perm
from .models import Lote
from linhagens.models import Linhagem
from historico.models import HistoricoEvento
from .forms import LoteForm


class LoteListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Lote
    template_name = "lotes/lote_list.html"
    context_object_name = "lotes"
    paginate_by = 20
    permission_required = "lotes.view_lote"
    search_fields = ["nome", "codigo", "local"]
    filter_fields = ["finalidade", "status", "linhagem_principal"]

    def get_queryset(self):
        return super().get_queryset().select_related("linhagem_principal")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["comparativo"] = Lote.objects.aggregate(
            media_quantidade=Avg("quantidade_atual"),
            media_custo=Avg("custo_acumulado"),
        )
        ctx["linhagens_filtro"] = (
            Linhagem.objects.filter(lotes__isnull=False).distinct().order_by("nome")
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
        ctx["painel_operacional"] = {
            "aves": len(aves),
            "vacinas_pendentes": sum(1 for vac in vacinas if vac.status == "pendente"),
            "tratamentos_ativos": len(tratamentos),
            "movimentos": len(movimentos),
            "nascimentos": len(nascimentos),
            "incubacoes": total_incubacoes,
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

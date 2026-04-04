from django.urls import reverse_lazy
from django.views import generic

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin, user_has_role_or_perm
from .models import Ave
from historico.models import HistoricoEvento
from .forms import AveForm


class AveListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Ave
    template_name = "aves/ave_list.html"
    context_object_name = "aves"
    paginate_by = 20
    permission_required = "aves.view_ave"
    search_fields = ["codigo_interno", "identificacao", "nome", "origem"]
    filter_fields = ["finalidade", "status", "linhagem"]

    def get_queryset(self):
        return super().get_queryset().select_related("linhagem", "lote_atual")


class AveDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = Ave
    template_name = "aves/ave_detail.html"
    context_object_name = "ave"
    permission_required = "aves.view_ave"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("linhagem", "lote_atual", "pai", "mae")
            .prefetch_related(
                "filhos_pai",
                "filhos_mae",
                "vendas",
                "abates",
                "incubacoes_matriz",
                "vacinas__vacina",
                "tratamentos__medicamento",
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ave = self.object
        user = self.request.user
        can_view_historico = bool(user and user.is_authenticated and user.is_manager)
        can_view_sanidade = user_has_role_or_perm(
            user,
            ["sanidade.view_aplicacaovacina", "sanidade.view_tratamento"],
        )
        can_view_vendas = user_has_role_or_perm(user, "vendas.view_venda")
        can_view_abates = user_has_role_or_perm(user, "abate.view_abate")
        vacinas = list(ave.vacinas.all())
        tratamentos = list(ave.tratamentos.all())
        vendas = list(ave.vendas.all())
        abates = list(ave.abates.all())
        incubacoes = list(ave.incubacoes_matriz.all())
        ctx["vacinas"] = vacinas if can_view_sanidade else []
        ctx["tratamentos"] = tratamentos if can_view_sanidade else []
        ctx["vendas"] = vendas if can_view_vendas else []
        ctx["abates"] = abates if can_view_abates else []
        ctx["historico"] = (
            HistoricoEvento.objects.filter(entidade="Ave", referencia_id=ave.pk)[:50]
            if can_view_historico
            else []
        )
        filhos_pai = list(ave.filhos_pai.all()[:10])
        filhos_pai_ids = {filho.pk for filho in filhos_pai}
        filhos_mae = [filho for filho in ave.filhos_mae.all()[:10] if filho.pk not in filhos_pai_ids]
        ctx["arvore_genetica"] = {
            "pai": ave.pai,
            "mae": ave.mae,
            "descendentes": (filhos_pai + filhos_mae)[:10],
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
        if ave.data_nascimento:
            timeline.append(
                {
                    "data": ave.data_nascimento,
                    "tipo": "Nascimento",
                    "descricao": "Nascimento cadastrado no perfil da ave",
                }
            )
        if ave.finalidade == Ave.FINALIDADE_REPRODUCAO:
            timeline.append(
                {
                    "data": ave.created_at.date(),
                    "tipo": "Reprodução",
                    "descricao": "Ave marcada com finalidade reprodutiva",
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
        for inc in incubacoes[:20]:
            timeline.append(
                {
                    "data": inc.data_entrada,
                    "tipo": "Incubação",
                    "descricao": f"Matriz ligada à incubação {inc.codigo}",
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
                        "descricao": f"Abate com peso total {abate.peso_total}",
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
        ctx["timeline_ave"] = sorted(
            [item for item in timeline if item.get("data")],
            key=lambda item: item["data"],
            reverse=True,
        )[:50]
        ctx["can_view_historico"] = can_view_historico
        ctx["can_view_sanidade"] = can_view_sanidade
        ctx["can_view_vendas"] = can_view_vendas
        ctx["can_view_abates"] = can_view_abates
        return ctx


class AveCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = Ave
    form_class = AveForm
    template_name = "aves/ave_form.html"
    success_url = reverse_lazy("aves:list")
    permission_required = "aves.add_ave"


class AveUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = Ave
    form_class = AveForm
    template_name = "aves/ave_form.html"
    success_url = reverse_lazy("aves:list")
    permission_required = "aves.change_ave"


class AveDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = Ave
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("aves:list")
    permission_required = "aves.delete_ave"

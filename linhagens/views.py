from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Sum, Q

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin
from .models import Linhagem
from .forms import LinhagemForm
from incubacao.models import Incubacao
from nascimentos.models import Nascimento


class LinhagemListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Linhagem
    template_name = "linhagens/linhagem_list.html"
    context_object_name = "linhagens"
    paginate_by = 20
    permission_required = "linhagens.view_linhagem"
    search_fields = ["nome", "origem"]
    filter_fields = ["ativo"]


class LinhagemDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = Linhagem
    template_name = "linhagens/linhagem_detail.html"
    context_object_name = "linhagem"
    permission_required = "linhagens.view_linhagem"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        linhagem = self.object
        aves = linhagem.aves.all()
        lotes = linhagem.lotes.all()
        incubacoes = Incubacao.objects.filter(
            Q(matriz_responsavel__linhagem=linhagem) | Q(lote_relacionado__linhagem_principal=linhagem)
        ).distinct()
        nascimentos = Nascimento.objects.filter(linhagem=linhagem)
        total_ovos = incubacoes.aggregate(total=Sum("quantidade_ovos"))["total"] or 0
        total_nascidos = nascimentos.aggregate(total=Sum("quantidade_nascida"))["total"] or 0
        total_fertis = incubacoes.aggregate(total=Sum("ovos_fertis"))["total"] or 0
        taxa_eclosao = 0
        if total_fertis:
            taxa_eclosao = (total_nascidos / total_fertis) * 100
        fertilidade = 0
        if total_ovos:
            fertilidade = (total_fertis / total_ovos) * 100
        consumo_total = sum((lote.consumo_racao_total or 0) for lote in lotes)
        custo_total = sum((lote.custo_acumulado or 0) for lote in lotes)
        produtividade = 0
        total_aves = aves.count()
        if total_aves:
            produtividade = total_nascidos / total_aves
        ctx["indicadores"] = {
            "total_aves": total_aves,
            "total_lotes": lotes.count(),
            "incubacoes": incubacoes.count(),
            "nascimentos": nascimentos.count(),
            "fertilidade": fertilidade,
            "taxa_eclosao": taxa_eclosao,
            "total_nascidos": total_nascidos,
            "consumo_medio": (consumo_total / lotes.count()) if lotes.exists() else 0,
            "produtividade": produtividade,
            "custo_total": custo_total,
        }
        return ctx


class LinhagemCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = Linhagem
    form_class = LinhagemForm
    template_name = "linhagens/linhagem_form.html"
    success_url = reverse_lazy("linhagens:list")
    permission_required = "linhagens.add_linhagem"


class LinhagemUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = Linhagem
    form_class = LinhagemForm
    template_name = "linhagens/linhagem_form.html"
    success_url = reverse_lazy("linhagens:list")
    permission_required = "linhagens.change_linhagem"


class LinhagemDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = Linhagem
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("linhagens:list")
    permission_required = "linhagens.delete_linhagem"

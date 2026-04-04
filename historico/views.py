from django.views import generic
from core.mixins import AuthenticatedView, ManagerOrAdminMixin, SearchFilterMixin
from .models import HistoricoEvento


class HistoricoListView(ManagerOrAdminMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):       
    model = HistoricoEvento
    template_name = "historico/historico_list.html"
    context_object_name = "eventos"
    paginate_by = 20
    permission_required = "historico.view_historicoevento"
    search_fields = ["entidade", "descricao"]
    filter_fields = ["entidade"]

    def get_queryset(self):
        qs = super().get_queryset().select_related("usuario")
        tipo = self.request.GET.get("tipo")
        if tipo == "acessos":
            qs = qs.filter(entidade="Permissao")
            categoria = self.request.GET.get("categoria")
            if categoria:
                qs = qs.filter(detalhes__tipo=categoria)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tipo"] = self.request.GET.get("tipo", "geral")
        ctx["categoria"] = self.request.GET.get("categoria", "")
        return ctx

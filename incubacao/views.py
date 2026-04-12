from django.urls import reverse_lazy
from django.views import generic

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin
from .models import Incubacao
from .forms import IncubacaoForm


class IncubacaoListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Incubacao
    template_name = "incubacao/incubacao_list.html"
    context_object_name = "incubacoes"
    paginate_by = 20
    permission_required = "incubacao.view_incubacao"
    search_fields = ["codigo", "origem_ovos"]
    filter_fields = ["tipo", "status", "lote_relacionado"]

    def get_queryset(self):
        return super().get_queryset().select_related("lote_relacionado")


class IncubacaoDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = Incubacao
    template_name = "incubacao/incubacao_detail.html"
    context_object_name = "incubacao"
    permission_required = "incubacao.view_incubacao"


class IncubacaoCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = Incubacao
    form_class = IncubacaoForm
    template_name = "incubacao/incubacao_form.html"
    success_url = reverse_lazy("incubacao:list")
    permission_required = "incubacao.add_incubacao"


class IncubacaoUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = Incubacao
    form_class = IncubacaoForm
    template_name = "incubacao/incubacao_form.html"
    success_url = reverse_lazy("incubacao:list")
    permission_required = "incubacao.change_incubacao"


class IncubacaoDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = Incubacao
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("incubacao:list")
    permission_required = "incubacao.delete_incubacao"

from django.urls import reverse_lazy
from django.views import generic

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin
from .models import Nascimento
from .forms import NascimentoForm


class NascimentoListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Nascimento
    template_name = "nascimentos/nascimento_list.html"
    context_object_name = "nascimentos"
    paginate_by = 20
    permission_required = "nascimentos.view_nascimento"
    search_fields = ["incubacao__codigo", "lote_destino__nome"]
    filter_fields = ["lote_destino"]


class NascimentoDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = Nascimento
    template_name = "nascimentos/nascimento_detail.html"
    context_object_name = "nascimento"
    permission_required = "nascimentos.view_nascimento"


class NascimentoCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = Nascimento
    form_class = NascimentoForm
    template_name = "nascimentos/nascimento_form.html"
    success_url = reverse_lazy("nascimentos:list")
    permission_required = "nascimentos.add_nascimento"


class NascimentoUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = Nascimento
    form_class = NascimentoForm
    template_name = "nascimentos/nascimento_form.html"
    success_url = reverse_lazy("nascimentos:list")
    permission_required = "nascimentos.change_nascimento"


class NascimentoDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = Nascimento
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("nascimentos:list")
    permission_required = "nascimentos.delete_nascimento"

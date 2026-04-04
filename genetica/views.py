from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin
from .models import RegistroGenetico
from .forms import RegistroGeneticoForm


class RegistroListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = RegistroGenetico
    template_name = "genetica/registro_list.html"
    context_object_name = "registros"
    paginate_by = 20
    permission_required = "genetica.view_registrogenetico"
    search_fields = ["filho__codigo_interno", "pai__codigo_interno", "mae__codigo_interno"]


class RegistroDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = RegistroGenetico
    template_name = "genetica/registro_detail.html"
    context_object_name = "registro"
    permission_required = "genetica.view_registrogenetico"


class RegistroCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = RegistroGenetico
    form_class = RegistroGeneticoForm
    template_name = "genetica/registro_form.html"
    success_url = reverse_lazy("genetica:list")
    permission_required = "genetica.add_registrogenetico"

    def form_valid(self, form):
        response = super().form_valid(form)
        if getattr(form, "consanguinidade_alerta", ""):
            messages.warning(self.request, form.consanguinidade_alerta)
        else:
            messages.success(self.request, "Registro genético salvo com sucesso.")
        return response


class RegistroUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = RegistroGenetico
    form_class = RegistroGeneticoForm
    template_name = "genetica/registro_form.html"
    success_url = reverse_lazy("genetica:list")
    permission_required = "genetica.change_registrogenetico"

    def form_valid(self, form):
        response = super().form_valid(form)
        if getattr(form, "consanguinidade_alerta", ""):
            messages.warning(self.request, form.consanguinidade_alerta)
        else:
            messages.success(self.request, "Registro genético atualizado com sucesso.")
        return response


class RegistroDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = RegistroGenetico
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("genetica:list")
    permission_required = "genetica.delete_registrogenetico"

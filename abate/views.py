from django.urls import reverse_lazy
from django.views import generic

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin
from .models import Abate
from .forms import AbateForm


class AbateListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Abate
    template_name = "abate/abate_list.html"
    context_object_name = "abates"
    paginate_by = 20
    permission_required = "abate.view_abate"
    search_fields = ["lote__nome"]
    filter_fields = ["lote"]


class AbateDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = Abate
    template_name = "abate/abate_detail.html"
    context_object_name = "abate"
    permission_required = "abate.view_abate"


class AbateCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = Abate
    form_class = AbateForm
    template_name = "abate/abate_form.html"
    success_url = reverse_lazy("abate:list")
    permission_required = "abate.add_abate"


class AbateUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = Abate
    form_class = AbateForm
    template_name = "abate/abate_form.html"
    success_url = reverse_lazy("abate:list")
    permission_required = "abate.change_abate"


class AbateDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = Abate
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("abate:list")
    permission_required = "abate.delete_abate"

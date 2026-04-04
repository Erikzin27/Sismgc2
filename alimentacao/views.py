from django.urls import reverse_lazy
from django.views import generic

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin
from .models import FormulaRacao
from .forms import FormulaRacaoForm


class FormulaListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = FormulaRacao
    template_name = "alimentacao/formula_list.html"
    context_object_name = "formulas"
    paginate_by = 20
    permission_required = "alimentacao.view_formularacao"
    search_fields = ["nome"]
    filter_fields = ["fase"]


class FormulaCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = FormulaRacao
    form_class = FormulaRacaoForm
    template_name = "alimentacao/formula_form.html"
    success_url = reverse_lazy("alimentacao:list")
    permission_required = "alimentacao.add_formularacao"


class FormulaUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = FormulaRacao
    form_class = FormulaRacaoForm
    template_name = "alimentacao/formula_form.html"
    success_url = reverse_lazy("alimentacao:list")
    permission_required = "alimentacao.change_formularacao"


class FormulaDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = FormulaRacao
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("alimentacao:list")
    permission_required = "alimentacao.delete_formularacao"

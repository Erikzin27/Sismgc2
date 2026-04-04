from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin
from .models import Venda
from .forms import VendaForm
from financeiro.models import LancamentoFinanceiro


def _sync_venda_financeiro(venda):
    lancamento = getattr(venda, "lancamento_financeiro", None)
    if venda.status_pagamento != Venda.STATUS_PAGO:
        if lancamento:
            lancamento.delete()
        return

    defaults = {
        "data": venda.data,
        "tipo": LancamentoFinanceiro.TIPO_ENTRADA,
        "categoria": LancamentoFinanceiro.CAT_VENDA,
        "descricao": f"Venda: {venda.produto} - {venda.cliente}",
        "valor": venda.valor_total,
        "lote": venda.lote,
        "ave": venda.ave,
        "forma_pagamento": venda.forma_pagamento,
        "observacoes": venda.observacoes,
    }
    if lancamento:
        for field, value in defaults.items():
            setattr(lancamento, field, value)
        lancamento.save()
    else:
        LancamentoFinanceiro.objects.create(venda=venda, **defaults)


class VendaListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Venda
    template_name = "vendas/venda_list.html"
    context_object_name = "vendas"
    paginate_by = 20
    permission_required = "vendas.view_venda"
    search_fields = ["cliente", "produto"]
    filter_fields = ["categoria", "status_pagamento"]


class VendaDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = Venda
    template_name = "vendas/venda_detail.html"
    context_object_name = "venda"
    permission_required = "vendas.view_venda"


class VendaCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = Venda
    form_class = VendaForm
    template_name = "vendas/venda_form.html"
    success_url = reverse_lazy("vendas:list")
    permission_required = "vendas.add_venda"

    def form_valid(self, form):
        response = super().form_valid(form)
        try:
            _sync_venda_financeiro(self.object)
            messages.success(self.request, "Venda salva com sucesso.")
        except Exception:
            messages.warning(
                self.request,
                "Venda salva com sucesso, mas não foi possível sincronizar com o financeiro agora.",
            )
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a venda. Verifique os campos destacados.")
        return super().form_invalid(form)


class VendaUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = Venda
    form_class = VendaForm
    template_name = "vendas/venda_form.html"
    success_url = reverse_lazy("vendas:list")
    permission_required = "vendas.change_venda"

    def form_valid(self, form):
        response = super().form_valid(form)
        try:
            _sync_venda_financeiro(self.object)
            messages.success(self.request, "Venda atualizada com sucesso.")
        except Exception:
            messages.warning(
                self.request,
                "Venda atualizada com sucesso, mas não foi possível sincronizar com o financeiro agora.",
            )
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a venda. Verifique os campos destacados.")
        return super().form_invalid(form)


class VendaDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = Venda
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("vendas:list")
    permission_required = "vendas.delete_venda"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        lancamento = getattr(self.object, "lancamento_financeiro", None)
        if lancamento:
            lancamento.delete()
        messages.success(request, "Venda excluída com sucesso.")
        return super().delete(request, *args, **kwargs)

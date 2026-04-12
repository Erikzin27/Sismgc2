from django.urls import reverse_lazy
from django.views import generic
from django.db import models
from django.utils import timezone
from datetime import timedelta

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin
from core.services.config import get_configuracao_sistema
from .models import ItemEstoque, MovimentoEstoque
from .forms import ItemEstoqueForm, MovimentoEstoqueForm


def _dias_alerta_vencimento():
    try:
        cfg = get_configuracao_sistema()
        return int(cfg.dias_alerta_vencimento) if cfg else 30
    except Exception:
        return 30


class ItemListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = ItemEstoque
    template_name = "estoque/item_list.html"
    context_object_name = "itens"
    paginate_by = 20
    permission_required = "estoque.view_itemestoque"
    search_fields = ["nome", "fornecedor"]
    filter_fields = ["categoria"]

    def get_queryset(self):
        from django.db.models import Case, IntegerField, Value, When, F

        qs = super().get_queryset()
        fornecedor = self.request.GET.get("fornecedor", "").strip()
        if fornecedor:
            qs = qs.filter(fornecedor__icontains=fornecedor)
        baixo = self.request.GET.get("baixo", "").strip()
        if baixo == "1":
            qs = qs.filter(quantidade_atual__lte=models.F("estoque_minimo"))
        venc = self.request.GET.get("vencimento", "").strip()
        hoje = timezone.localdate()
        dias = _dias_alerta_vencimento()
        vencendo_ate = hoje + timedelta(days=int(dias))
        if venc == "vencido":
            qs = qs.filter(validade__lt=hoje)
        elif venc == "vencendo":
            qs = qs.filter(validade__gte=hoje, validade__lte=vencendo_ate)
        qs = qs.annotate(
            _rank=Case(
                When(validade__isnull=False, validade__lt=hoje, then=Value(0)),
                When(validade__isnull=False, validade__range=(hoje, vencendo_ate), then=Value(1)),
                When(quantidade_atual__lte=F("estoque_minimo"), then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by("_rank", "nome")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoje = timezone.localdate()
        dias = _dias_alerta_vencimento()
        vencendo_ate = hoje + timedelta(days=int(dias))
        ctx["itens_baixos"] = ItemEstoque.objects.filter(quantidade_atual__lte=models.F("estoque_minimo")).count()
        ctx["itens_vencidos"] = ItemEstoque.objects.filter(validade__lt=hoje).count()
        ctx["itens_vencendo"] = ItemEstoque.objects.filter(validade__gte=hoje, validade__lte=vencendo_ate).count()
        return ctx


class ItemDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = ItemEstoque
    template_name = "estoque/item_detail.html"
    context_object_name = "item"
    permission_required = "estoque.view_itemestoque"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["movimentos"] = (
            MovimentoEstoque.objects.filter(item=self.object)
            .select_related("item", "lote_relacionado")
            .order_by("-data", "-created_at")[:10]
        )
        return ctx


class ItemCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = ItemEstoque
    form_class = ItemEstoqueForm
    template_name = "estoque/item_form.html"
    success_url = reverse_lazy("estoque:list")
    permission_required = "estoque.add_itemestoque"


class ItemUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = ItemEstoque
    form_class = ItemEstoqueForm
    template_name = "estoque/item_form.html"
    success_url = reverse_lazy("estoque:list")
    permission_required = "estoque.change_itemestoque"


class ItemDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = ItemEstoque
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("estoque:list")
    permission_required = "estoque.delete_itemestoque"


class MovimentoListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):   
    model = MovimentoEstoque
    template_name = "estoque/movimento_list.html"
    context_object_name = "movimentos"
    paginate_by = 20
    permission_required = "estoque.view_movimentoestoque"
    search_fields = ["item__nome", "observacoes"]
    filter_fields = ["tipo", "item", "motivo"]

    def get_queryset(self):
        qs = super().get_queryset().select_related("item", "lote_relacionado")
        fornecedor = self.request.GET.get("fornecedor", "").strip()
        if fornecedor:
            qs = qs.filter(fornecedor__icontains=fornecedor)
        lote = self.request.GET.get("lote", "").strip()
        if lote:
            qs = qs.filter(lote_relacionado__id=lote)
        ini = self.request.GET.get("inicio", "").strip()
        fim = self.request.GET.get("fim", "").strip()
        if ini:
            qs = qs.filter(data__gte=ini)
        if fim:
            qs = qs.filter(data__lte=fim)
        return qs


class MovimentoCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = MovimentoEstoque
    form_class = MovimentoEstoqueForm
    template_name = "estoque/movimento_form.html"
    success_url = reverse_lazy("estoque:mov_list")
    permission_required = "estoque.add_movimentoestoque"

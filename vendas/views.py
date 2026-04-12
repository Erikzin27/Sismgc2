from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.utils import timezone
import logging

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin
from .models import Venda
from .forms import VendaForm
from financeiro.models import LancamentoFinanceiro

logger = logging.getLogger(__name__)


def _sync_venda_financeiro(venda):
    """
    Sincroniza a venda com o financeiro.
    
    Regras:
    - Se venda paga: cria/atualiza entrada
    - Se não paga: remove entrada (se existir)
    - Evita duplicidade com OneToOneField
    - Loga tudo para auditoria
    
    Args:
        venda: Instância de Venda
        
    Raises:
        Exception: Se houver erro crítico na sincronização
    """
    try:
        lancamento = getattr(venda, "lancamento_financeiro", None)
        
        # Se venda não está paga, remove entrada se existir
        if venda.status_pagamento != Venda.STATUS_PAGO:
            if lancamento:
                lancamento.delete()
                logger.info(f"Vendas: Venda #{venda.pk} não paga - lançamento financeiro removido")
            return

        # Se venda está paga, atualiza ou cria entrada
        defaults = {
            "data": venda.data,
            "tipo": LancamentoFinanceiro.TIPO_ENTRADA,
            "categoria": LancamentoFinanceiro.CAT_VENDA,
            "descricao": f"Venda: {venda.produto} - Cliente: {venda.cliente}",
            "valor": venda.valor_total,
            "lote": venda.lote,
            "ave": venda.ave,
            "forma_pagamento": venda.forma_pagamento,
            "observacoes": f"Vinculada à venda #{venda.pk}" + (f"\n{venda.observacoes}" if venda.observacoes else ""),
        }
        
        if lancamento:
            # Atualizar lançamento existente
            for field, value in defaults.items():
                setattr(lancamento, field, value)
            lancamento.save()
            logger.info(f"Vendas: Venda #{venda.pk} - lançamento financeiro #{lancamento.pk} atualizado")
        else:
            # Criar novo lançamento
            lancamento = LancamentoFinanceiro.objects.create(venda=venda, **defaults)
            logger.info(f"Vendas: Venda #{venda.pk} - novo lançamento financeiro #{lancamento.pk} criado")
    
    except LancamentoFinanceiro.MultipleObjectsReturned:
        logger.error(f"Vendas: Venda #{venda.pk} - ERRO: múltiplos lançamentos encontrados (inconsistência de dados)")
        raise
    
    except Exception as e:
        logger.error(f"Vendas: Venda #{venda.pk} - ERRO ao sincronizar com financeiro: {str(e)}")
        raise


class VendaListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Venda
    template_name = "vendas/venda_list.html"
    context_object_name = "vendas"
    paginate_by = 20
    permission_required = "vendas.view_venda"
    search_fields = ["cliente", "produto"]
    filter_fields = ["categoria", "status_pagamento"]

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true":
            return ["vendas/_venda_table.html"]
        return [self.template_name]

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("lote", "ave", "lancamento_financeiro")
            .only(
                "id", "data", "cliente", "produto", "categoria", 
                "quantidade", "valor_unitario", "desconto", "valor_total",
                "status_pagamento", "forma_pagamento",
                "lote__id", "lote__nome", "lote__codigo",
                "ave__id", "ave__identificacao",
                "lancamento_financeiro__id", "lancamento_financeiro__valor"
            )
        )
        forma_pagamento = self.request.GET.get("forma_pagamento", "").strip()
        if forma_pagamento:
            qs = qs.filter(forma_pagamento__iexact=forma_pagamento)
        lote = self.request.GET.get("lote", "").strip()
        if lote:
            qs = qs.filter(lote_id=lote)
        inicio = self.request.GET.get("inicio", "").strip()
        fim = self.request.GET.get("fim", "").strip()
        if inicio:
            qs = qs.filter(data__gte=inicio)
        if fim:
            qs = qs.filter(data__lte=fim)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        resumo = queryset.aggregate(
            total_valor=Sum("valor_total"),
            total_quantidade=Sum("quantidade"),
            total_vendas=Count("id", distinct=True),
            vendas_pagas=Count("id", filter=Q(status_pagamento=Venda.STATUS_PAGO), distinct=True),
            vendas_pendentes=Count("id", filter=Q(status_pagamento=Venda.STATUS_PENDENTE), distinct=True),
            vendas_com_entrada=Count("id", filter=Q(lancamento_financeiro__isnull=False), distinct=True),
        )
        ctx.update(
            {
                "total_vendas": resumo["total_vendas"] or 0,
                "total_valor": resumo["total_valor"] or 0,
                "total_quantidade": resumo["total_quantidade"] or 0,
                "vendas_pagas": resumo["vendas_pagas"] or 0,
                "vendas_pendentes": resumo["vendas_pendentes"] or 0,
                "vendas_com_entrada": resumo["vendas_com_entrada"] or 0,
            }
        )
        
        # Cache filtros apenas se não for AJAX
        if self.request.headers.get("HX-Request") != "true":
            ctx["lotes_filtro"] = (
                Venda.objects
                .values_list("lote__id", "lote__nome")
                .filter(lote__isnull=False)
                .distinct()
                .order_by("lote__nome")
            )
            ctx["formas_pagamento_filtro"] = (
                queryset
                .exclude(forma_pagamento="")
                .values_list("forma_pagamento", flat=True)
                .distinct()
                .order_by("forma_pagamento")
            )
        return ctx


class VendaDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = Venda
    template_name = "vendas/venda_detail.html"
    context_object_name = "venda"
    permission_required = "vendas.view_venda"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        venda = self.object
        hoje = timezone.localdate()
        meses = []
        ano = hoje.year
        mes = hoje.month
        for _ in range(6):
            meses.append((ano, mes))
            mes -= 1
            if mes == 0:
                mes = 12
                ano -= 1
        meses.reverse()
        labels = [f"{m:02d}/{a}" for a, m in meses]
        serie = []
        for a, m in meses:
            total = (
                Venda.objects.filter(data__year=a, data__month=m)
                .aggregate(total=Sum("valor_total"))["total"]
                or 0
            )
            serie.append(float(total))
        ctx["venda_chart"] = {"labels": labels, "series": serie}
        impacto = float(venda.valor_total or 0) if venda.status_pagamento == Venda.STATUS_PAGO else 0
        ctx["impacto_caixa"] = impacto
        sugestoes = []
        if venda.status_pagamento == Venda.STATUS_PENDENTE:
            sugestoes.append("Venda pendente: enviar cobrança ou confirmar pagamento.")
        if venda.status_pagamento == Venda.STATUS_PAGO and not venda.lancamento_financeiro:
            sugestoes.append("Venda paga sem entrada no financeiro. Gerar vínculo.")
        if venda.lancamento_financeiro:
            sugestoes.append("Entrada financeira já vinculada. Conferir comprovante.")
        ctx["sugestoes_venda"] = sugestoes
        return ctx


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
            if self.object.status_pagamento == Venda.STATUS_PAGO:
                if self.object.tem_entrada_financeira:
                    messages.success(self.request, "Venda criada e entrada financeira gerada com sucesso.")
                else:
                    messages.warning(
                        self.request,
                        "Venda criada com sucesso, mas a entrada no financeiro está pendente. Tente novamente.",
                    )
            else:
                messages.success(self.request, "Venda criada com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao sincronizar venda #{self.object.pk}: {str(e)}")
            messages.warning(
                self.request,
                "Venda salva com sucesso, mas houve um erro ao sincronizar com o financeiro. Tente sincronizar novamente.",
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
            if self.object.status_pagamento == Venda.STATUS_PAGO:
                if self.object.tem_entrada_financeira:
                    messages.success(self.request, "Venda atualizada e entrada financeira sincronizada com sucesso.")
                else:
                    messages.warning(
                        self.request,
                        "Venda atualizada com sucesso, mas a entrada no financeiro está pendente. Tente novamente.",
                    )
            else:
                messages.success(self.request, "Venda atualizada com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao sincronizar venda #{self.object.pk}: {str(e)}")
            messages.warning(
                self.request,
                "Venda atualizada com sucesso, mas houve um erro ao sincronizar com o financeiro. Tente sincronizar novamente.",
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
        venda_pk = self.object.pk
        
        lancamento = getattr(self.object, "lancamento_financeiro", None)
        if lancamento:
            try:
                lancamento_pk = lancamento.pk
                lancamento.delete()
                messages.info(request, f"Venda excluída. Lançamento financeiro #{lancamento_pk} também removido.")
                logger.info(f"Venda #{venda_pk}: Deletada junto com lançamento financeiro #{lancamento_pk}")
            except Exception as e:
                logger.error(f"Erro ao deletar lançamento financeiro da venda #{venda_pk}: {str(e)}")
                messages.warning(request, "Venda excluída, mas houve erro ao remover entrada no financeiro.")
        else:
            messages.success(request, "Venda excluída com sucesso.")
            logger.info(f"Venda #{venda_pk}: Deletada (sem lançamento financeiro vinculado)")
        
        return super().delete(request, *args, **kwargs)

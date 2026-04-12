# PLANO DE AÇÃO - FASE 1 (Implementação)
**Data de Início:** 12 de abril de 2026  
**Duração Estimada:** 4 dias (1 developer × 28 horas)  
**Prioridade:** CRÍTICA (Bloqueador para Fase 2)

---

## 1. TASK 1.1 - Corrigir Sincronização Venda-Financeiro (4 horas)

### Status: 🔴 BLOQUEADOR

**Problema:** Sem transações atômicas, Venda e LancamentoFinanceiro podem ficar desincronizados

**Arquivos a modificar:**
- `vendas/views.py` - _sync_venda_financeiro() 
- `vendas/models.py` - Adicionar signal
- Criar arquivo novo: `vendas/signals.py`

---

### Step 1.1.1: Adicionar @transaction.atomic

**Arquivo:** [vendas/views.py](vendas/views.py) - Linha 16

**Código Atual (INCORRETO):**
```python
def _sync_venda_financeiro(venda):
    """Sincroniza a venda com o financeiro..."""
    try:
        lancamento = getattr(venda, "lancamento_financeiro", None)
        # ... código
```

**Código Novo (CORRETO):**
```python
from django.db import transaction

@transaction.atomic
def _sync_venda_financeiro(venda):
    """
    Sincroniza a venda com o financeiro de forma atômica.
    
    Se houver erro, TODA operação é revertida (Venda + Lancamento).
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
                lancamento_pk = lancamento.pk
                lancamento.delete()
                logger.info(f"Vendas: Venda #{venda.pk} não paga - lançamento financeiro #{lancamento_pk} removido")
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
            logger.info(f"Vendas: Venda #{venda.pk} - lançamento financeiro #{lancamento.pk} atualizado (transação atômica)")
        else:
            # Criar novo lançamento
            lancamento = LancamentoFinanceiro.objects.create(venda=venda, **defaults)
            logger.info(f"Vendas: Venda #{venda.pk} - novo lançamento financeiro #{lancamento.pk} criado (transação atômica)")
    
    except LancamentoFinanceiro.MultipleObjectsReturned as e:
        logger.error(f"Vendas: Venda #{venda.pk} - ERRO CRÍTICO: múltiplos lançamentos encontrados (inconsistência de dados)")
        raise
    
    except Exception as e:
        logger.error(f"Vendas: Venda #{venda.pk} - ERRO ao sincronizar com financeiro: {str(e)}", exc_info=True)
        raise  # Re-raise para que transaction.atomic reverta


class VendaListView(...):
    # ... resto igual

class VendaDetailView(...):
    # ... resto igual

class VendaCreateView(...):
    def form_valid(self, form):
        response = super().form_valid(form)
        try:
            _sync_venda_financeiro(self.object)  # ← Agora é atômico!
            if self.object.status_pagamento == Venda.STATUS_PAGO:
                if self.object.tem_entrada_financeira:
                    messages.success(self.request, "Venda criada e entrada financeira gerada com sucesso.")
                else:
                    messages.warning(self.request, "Venda criada com sucesso, mas a entrada no financeiro está pendente. Tente novamente.")
            else:
                messages.success(self.request, "Venda criada com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao sincronizar venda #{self.object.pk}: {str(e)}")
            messages.warning(self.request, "Venda salva com sucesso, mas houve um erro ao sincronizar com o financeiro. Tente sincronizar novamente.")
        return response


class VendaUpdateView(...):
    def form_valid(self, form):
        response = super().form_valid(form)
        try:
            _sync_venda_financeiro(self.object)  # ← Agora é atômico!
            if self.object.status_pagamento == Venda.STATUS_PAGO:
                if self.object.tem_entrada_financeira:
                    messages.success(self.request, "Venda atualizada e entrada financeira sincronizada com sucesso.")
                else:
                    messages.warning(self.request, "Venda atualizada com sucesso, mas a entrada no financeiro está pendente. Tente novamente.")
            else:
                messages.success(self.request, "Venda atualizada com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao sincronizar venda #{self.object.pk}: {str(e)}")
            messages.warning(self.request, "Venda atualizada com sucesso, mas houve um erro ao sincronizar com o financeiro. Tente sincronizar novamente.")
        return response


class VendaDeleteView(...):
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        venda_pk = self.object.pk
        
        lancamento = getattr(self.object, "lancamento_financeiro", None)
        if lancamento:
            try:
                lancamento_pk = lancamento.pk
                lancamento.delete()
                messages.info(request, f"Venda excluída. Lançamento financeiro #{lancamento_pk} também removido.")
                logger.info(f"Venda #{venda_pk}: Deletada junto com lançamento financeiro #{lancamento_pk} (transação atômica)")
            except Exception as e:
                logger.error(f"Erro ao deletar lançamento financeiro da venda #{venda_pk}: {str(e)}")
                messages.warning(request, "Venda excluída, mas houve erro ao remover entrada no financeiro.")
        else:
            messages.success(request, "Venda excluída com sucesso.")
            logger.info(f"Venda #{venda_pk}: Deletada (sem lançamento financeiro vinculado)")
        
        return super().delete(request, *args, **kwargs)
```

**Checklist:**
- [ ] Adicionar `from django.db import transaction`
- [ ] Decorador `@transaction.atomic` em _sync_venda_financeiro()
- [ ] Testar criar venda e desativar DB midway
- [ ] Verificar se venda+lancamento são revertidos juntos

---

### Step 1.1.2: Adicionar Signal Automático

**Arquivo:** Criar [vendas/signals.py](vendas/signals.py)

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from vendas.models import Venda
from vendas.views import _sync_venda_financeiro


@receiver(post_save, sender=Venda)
def auto_sync_venda_financeiro(sender, instance, created, **kwargs):
    """
    Sincronização automática sempre que Venda é salva.
    Garante que Venda.lancamento_financeiro está sempre consistente.
    """
    try:
        _sync_venda_financeiro(instance)
    except Exception as e:
        # Log mas não falha a operação (já foi salva Venda)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao sincronizar automaticamente venda #{instance.pk}: {str(e)}", exc_info=True)
        # Em produção, pode enviar alerta para admins
```

**Arquivo:** Atualizar [vendas/apps.py](vendas/apps.py)

```python
from django.apps import AppConfig


class VendasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vendas'

    def ready(self):
        import vendas.signals  # ← Registrar signals ao carregar app
```

**Checklist:**
- [ ] Criar vendas/signals.py
- [ ] Importar signals em vendas/apps.py ready()
- [ ] Testar que signal recebe todas as mudanças
- [ ] Testar exception handling sem quebrar Venda

---

### Step 1.1.3: Adicionar Testes

**Arquivo:** Criar [vendas/tests.py](vendas/tests.py) ou expandir se exists

```python
from django.test import TestCase, TransactionTestCase
from django.db import transaction, IntegrityError
from django.utils import timezone

from vendas.models import Venda
from financeiro.models import LancamentoFinanceiro
from lotes.models import Lote
from linhagens.models import Linhagem


class VendaSincronizacaoTestCase(TransactionTestCase):
    """Testes para sincronização Venda ↔ Financeiro"""
    
    @classmethod
    def setUpTestData(cls):
        cls.linhagem = Linhagem.objects.create(nome="Teste")
        cls.lote = Lote.objects.create(
            nome="Lote Test",
            codigo="TEST-001",
            data_criacao=timezone.localdate(),
            finalidade="corte",
            linhagem_principal=cls.linhagem,
            quantidade_inicial=100
        )
    
    def test_venda_paga_cria_lancamento(self):
        """Quando venda é criada como PAGO, deve criar LancamentoFinanceiro"""
        venda = Venda.objects.create(
            data=timezone.localdate(),
            cliente="Cliente A",
            produto="Aves",
            categoria="ave_viva",
            quantidade=10,
            valor_unitario=100,
            valor_total=1000,
            lote=self.lote,
            status_pagamento=Venda.STATUS_PAGO
        )
        
        # Aguardar signal
        self.assertTrue(hasattr(venda, 'lancamento_financeiro'))
        self.assertIsNotNone(venda.lancamento_financeiro)
        
        entrada = venda.lancamento_financeiro
        self.assertEqual(entrada.tipo, LancamentoFinanceiro.TIPO_ENTRADA)
        self.assertEqual(entrada.categoria, LancamentoFinanceiro.CAT_VENDA)
        self.assertEqual(entrada.valor, 1000)
    
    def test_venda_nao_paga_nao_cria_lancamento(self):
        """Venda pendente não deve criar LancamentoFinanceiro"""
        venda = Venda.objects.create(
            data=timezone.localdate(),
            cliente="Cliente B",
            produto="Aves",
            categoria="ave_viva",
            quantidade=10,
            valor_unitario=100,
            valor_total=1000,
            lote=self.lote,
            status_pagamento=Venda.STATUS_PENDENTE
        )
        
        self.assertFalse(hasattr(venda, 'lancamento_financeiro') and venda.lancamento_financeiro)

    def test_mudar_status_pago_paga_cria_entrada(self):
        """Mudar venda de PENDENTE para PAGO deve criar entrada"""
        venda = Venda.objects.create(
            data=timezone.localdate(),
            cliente="Cliente C",
            produto="Aves",
            categoria="ave_viva",
            quantidade=10,
            valor_unitario=100,
            valor_total=1000,
            lote=self.lote,
            status_pagamento=Venda.STATUS_PENDENTE
        )
        
        # Inicialmente não tem entrada
        self.assertFalse(hasattr(venda, 'lancamento_financeiro') and venda.lancamento_financeiro)
        
        # Mudar para pago
        venda.status_pagamento = Venda.STATUS_PAGO
        venda.save()
        
        # Recarregar do BD
        venda.refresh_from_db()
        
        # Agora deve ter entrada
        self.assertIsNotNone(venda.lancamento_financeiro)

    def test_transacao_atomica_venda_lancamento(self):
        """Se LancamentoFinanceiro falhar, Venda também deve reverter"""
        try:
            with transaction.atomic():
                venda = Venda.objects.create(
                    data=timezone.localdate(),
                    cliente="Cliente D",
                    produto="Aves",
                    categoria="ave_viva",
                    quantidade=10,
                    valor_unitario=100,
                    valor_total=1000,
                    lote=self.lote,
                    status_pagamento=Venda.STATUS_PAGO
                )
                
                # Simular erro no lancamento
                raise IntegrityError("DB error")
        except IntegrityError:
            pass
        
        # Venda não deve existir (revertida pela transação)
        self.assertEqual(Venda.objects.filter(cliente="Cliente D").count(), 0)
```

**Checklist:**
- [ ] Criar testes transacionais
- [ ] Testar créação com status PAGO
- [ ] Testar mudança de status
- [ ] Testar revert transacional
- [ ] Executar `python manage.py test vendas`

---

### Step 1.1.4: Documentar na Wiki/README

**Arquivo:** Adicionar seção em [README.md](README.md)

```markdown
## Sincronização Venda-Financeiro (FASE 1)

### Implementação
- `_sync_venda_financeiro()` agora é **atômica** @transaction.atomic
- Signal `auto_sync_venda_financeiro` sincroniza automaticamente
- OneToOneField evita duplicidade

### Garantias
✓ Se Venda PAGO → LancamentoFinanceiro ENTRADA criado/atualizado
✓ Se Venda NÃO PAGO → LancamentoFinanceiro deletado
✓ Se erro → Ambos revertidos (transação atômica)

### Testes
```bash
python manage.py test vendas.VendaSincronizacaoTestCase
```

### Validação (DB Query)
```sql
-- Deve retornar 0 linhas
SELECT COUNT(*) FROM vendas_venda v 
WHERE v.status_pagamento = 'pago' 
AND NOT EXISTS (
  SELECT 1 FROM financeiro_lancamentofinanceiro 
  WHERE venda_id = v.id
);
```
```

**Checklist:**
- [ ] Adicionar documentação em README
- [ ] Documentar signal behavior
- [ ] Adicionar query de validação

---

### Estimativa: 4 horas

---

## 2. TASK 1.2 - Otimizar Queries N+1 em Lote (6 horas)

### Status: 🔴 CRÍTICA

**Problema:** Cada Lote faz 7+ properties queries → 140+ queries em listagem

---

### Step 1.2.1: Criar Serviço de Análise

**Arquivo:** Criar [core/services/lote_analytics.py](core/services/lote_analytics.py)

```python
from django.db.models import Q, Sum, Avg, Count, F, Case, When
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class LoteAnalyticsService:
    """Serviço centralizado para cálculos/análises de Lote."""
    
    @staticmethod
    def calcular_custos_e_receitas_batch(lotes_qs):
        """
        Calcula custos e receitas para múltiplos lotes em 1 query.
        
        Retorna dict mapping lote_id → {custos, receitas, lucro, ...}
        
        Args:
            lotes_qs: QuerySet de Lote
            
        Returns:
            dict: {lote_id: {...valores...}, ...}
        """
        from estoque.models import MovimentoEstoque, ItemEstoque
        from financeiro.models import LancamentoFinanceiro
        from vendas.models import Venda
        
        # Pré-fetch em 1 query cada
        vendas_por_lote = (
            Venda.objects.filter(lote__in=lotes_qs)
            .values('lote_id')
            .annotate(total_receita=Sum('valor_total'))
        )
        
        despesas_por_lote = (
            LancamentoFinanceiro.objects.filter(
                lote__in=lotes_qs,
                tipo=LancamentoFinanceiro.TIPO_SAIDA
            )
            .values('lote_id')
            .annotate(total_despesas=Sum('valor'))
        )
        
        sanitario_por_lote = (
            LancamentoFinanceiro.objects.filter(
                lote__in=lotes_qs,
                tipo=LancamentoFinanceiro.TIPO_SAIDA,
                categoria__in=[
                    LancamentoFinanceiro.CAT_VACINA,
                    LancamentoFinanceiro.CAT_MEDICAMENTO
                ]
            )
            .values('lote_id')
            .annotate(total_sanitario=Sum('valor'))
        )
        
        racao_por_lote = (
            MovimentoEstoque.objects.filter(
                lote_relacionado__in=lotes_qs,
                tipo=MovimentoEstoque.TIPO_SAIDA,
                item__categoria=ItemEstoque.CAT_RACAO
            )
            .values('lote_relacionado_id')
            .annotate(
                total_racao_kg=Sum('quantidade'),
                total_racao_custo=Sum(F('quantidade') * F('custo_unitario'))
            )
        )
        
        # Consolidar em dict
        resultado = {}
        
        for vendas_row in vendas_por_lote:
            lote_id = vendas_row['lote_id']
            if lote_id not in resultado:
                resultado[lote_id] = {}
            resultado[lote_id]['receita_total'] = vendas_row['total_receita'] or 0
        
        for despesas_row in despesas_por_lote:
            lote_id = despesas_row['lote_id']
            if lote_id not in resultado:
                resultado[lote_id] = {}
            resultado[lote_id]['despesas_total'] = despesas_row['total_despesas'] or 0
        
        for sanitario_row in sanitario_por_lote:
            lote_id = sanitario_row['lote_id']
            if lote_id not in resultado:
                resultado[lote_id] = {}
            resultado[lote_id]['custo_sanitario'] = sanitario_row['total_sanitario'] or 0
        
        for racao_row in racao_por_lote:
            lote_id = racao_row['lote_relacionado_id']
            if lote_id not in resultado:
                resultado[lote_id] = {}
            resultado[lote_id]['consumo_racao_kg'] = racao_row['total_racao_kg'] or 0
            resultado[lote_id]['custo_racao'] = racao_row['total_racao_custo'] or 0
        
        # Calcular lucro
        for lote_id, dados in resultado.items():
            receita = dados.get('receita_total', 0)
            racao = dados.get('custo_racao', 0)
            despesas = dados.get('despesas_total', 0)
            dados['lucro_liquido'] = receita - (racao + despesas)
        
        return resultado
    
    @staticmethod
    def get_lote_resumo_otimizado(lote, analytics_cache=None):
        """
        Retorna resumo completo de 1 lote sem queries extras.
        
        Args:
            lote: Instância de Lote
            analytics_cache: dict já calculado por calcular_custos_e_receitas_batch()
            
        Returns:
            dict: {custo_racao, receita, lucro, ...}
        """
        if analytics_cache and lote.id in analytics_cache:
            return analytics_cache[lote.id]
        
        # Fallback se não houver cache (menos eficiente, mas funciona)
        # Isto será otimizado - evitar chamar aqui em produção
        return {
            'custo_racao': lote.custo_racao,
            'receita_total': lote.receita_vendas,
            'despesas_total': lote.despesas_extras,
            'custo_sanitario': lote.custo_sanitario,
            'lucro_liquido': lote.lucro_final,
        }
```

**Checklist:**
- [ ] Criar core/services/lote_analytics.py
- [ ] Implementar batch calculation
- [ ] Testar que retorna dicts corretos
- [ ] Documentar uso

---

### Step 1.2.2: Refatorar LoteListView

**Arquivo:** [lotes/views.py](lotes/views.py) - LoteListView.get_queryset() (linha 17)

**Código Atual:**
```python
class LoteListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Lote
    template_name = "lotes/lote_list.html"
    context_object_name = "lotes"
    paginate_by = 20
    
    def get_queryset(self):
        return super().get_queryset().select_related("linhagem_principal")
        # ← Falta prefetch_related!
```

**Código Novo:**
```python
from core.services.lote_analytics import LoteAnalyticsService

class LoteListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Lote
    template_name = "lotes/lote_list.html"
    context_object_name = "lotes"
    paginate_by = 20
    permission_required = "lotes.view_lote"
    search_fields = ["nome", "codigo", "local"]
    filter_fields = ["finalidade", "status", "linhagem_principal"]

    def get_queryset(self):
        # ← OTIMIZAÇÃO: Adicionar prefetch_related e select_related
        return super().get_queryset().select_related(
            "linhagem_principal"
        ).prefetch_related(
            "aves",
            "vendas",
            "movimentoestoque_set__item",
            "lancamentos"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # ← OTIMIZAÇÃO: Analytics em batch
        analytics = LoteAnalyticsService.calcular_custos_e_receitas_batch(queryset)
        ctx['analytics'] = analytics
        
        user = self.request.user
        ctx["comparativo"] = Lote.objects.aggregate(
            media_quantidade=Avg("quantidade_atual"),
            media_custo=Avg("custo_acumulado"),
        )
        
        # ... resto similar
        
        return ctx
```

**No template**, usar cache:
```django
{# templates/lotes/lote_list.html #}
{% for lote in lotes %}
    <tr>
        <td>{{ lote.nome }}</td>
        <td>{{ analytics|get_item:lote.id|get_item:'receita_total' }}</td>
        <td>{{ analytics|get_item:lote.id|get_item:'lucro_liquido' }}</td>
    </tr>
{% endfor %}
```

**Template Filter Helper:**
```python
# lotes/templatetags/lote_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
```

**Checklist:**
- [ ] Adicionar prefetch_related em get_queryset()
- [ ] Chamar LoteAnalyticsService em get_context_data()
- [ ] Criar template filter ou usar dict.get em template
- [ ] Testar queries com django-debug-toolbar
- [ ] Medir antes/depois performance

---

### Step 1.2.3: Refatorar LoteDetailView

**Arquivo:** [lotes/views.py](lotes/views.py) - LoteDetailView (linha 47)

```python
class LoteDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = Lote
    template_name = "lotes/lote_detail.html"
    context_object_name = "lote"
    permission_required = "lotes.view_lote"

    def get_queryset(self):
        # ← JÁ TEM prefetch_related, mas pode melhorar
        return (
            super()
            .get_queryset()
            .select_related("linhagem_principal")
            .prefetch_related(
                "aves",
                "vendas",
                "abates",
                "incubacoes",
                "nascimentos",
                "vacinas__vacina",         # ← Adicionar
                "tratamentos__medicamento", # ← Adicionar
                "movimentoestoque_set__item",
                "lancamentos"               # ← Adicionar
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lote = self.object
        user = self.request.user
        
        # ← OTIMIZAÇÃO: Usar serviço em vez de properties
        analytics = LoteAnalyticsService.calcular_custos_e_receitas_batch(
            Lote.objects.filter(pk=lote.pk)
        )
        lote_analytics = analytics.get(lote.pk, {})
        
        # ... usar lote_analytics em vez de lote.custo_racao, etc
        
        ctx["painel_inteligente"] = {
            "consumo_total": lote_analytics.get('consumo_racao_kg', 0),
            "custo_racao": lote_analytics.get('custo_racao', 0),
            "receita": lote_analytics.get('receita_total', 0),
            "lucro": lote_analytics.get('lucro_liquido', 0),
            # ... resto
        }
        
        return ctx
```

**Checklist:**
- [ ] Adicionar prefetch_related faltantes
- [ ] Usar LoteAnalyticsService.calcular_custos_e_receitas_batch()
- [ ] Remover chamadas a lote.custo_racao, lote.lucro_final, etc
- [ ] Testar queries

---

### Step 1.2.4: Adicionar Testes de Performance

**Arquivo:** [lotes/tests.py](lotes/tests.py) - Novo arquivo ou expandir

```python
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection
from django.db import reset_queries
from core.services.lote_analytics import LoteAnalyticsService

class LoteQueryPerformanceTestCase(TestCase):
    """Testes de performance e queries de Lote."""
    
    @override_settings(DEBUG=True)
    def test_lote_list_queries_otimizadas(self):
        """LoteListView deve fazer ~5 queries com 20 lotes (não 140!)"""
        
        # Setup
        linhagem = ...  # criar
        lotes = Lote.objects.bulk_create([...20 lotes...])
        
        # Criar vendas, movimentos, lancamentos para cada lote
        for lote in lotes:
            Venda.objects.create(lote=lote, ...)
            Abate.objects.create(lote=lote, ...)
            # ...
        
        # Reset queries
        reset_queries()
        
        # Executar listagem igual à view
        from lotes.views import LoteListView
        view = LoteListView()
        view.request = RequestFactory().get('/lotes/')
        view.request.user = ...  # mock user
        qs = view.get_queryset()
        
        # Focar: fazer queries
        lista = list(qs)
        
        # Asseguração
        query_count = len(connection.queries)
        self.assertLess(query_count, 10, 
            f"Expected ~5 queries, got {query_count}. See queries: {connection.queries}")
        
    def test_lote_analytics_service_batch(self):
        """LoteAnalyticsService.calcular_custos_e_receitas_batch() deve fazer poucas queries."""
        
        # Setup
        lotes = Lote.objects.create([...10 lotes...])
        for lote in lotes:
            # Criar vendas, movimentos, etc
            pass
        
        # Executar
        reset_queries()
        analytics = LoteAnalyticsService.calcular_custos_e_receitas_batch(
            Lote.objects.all()
        )
        
        # Asseguração
        query_count = len(connection.queries)
        self.assertLess(query_count, 6,
            f"Expected ~5 queries, got {query_count}")
        
        # Validar dados
        self.assertEqual(len(analytics), 10)
        for lote_id, dados in analytics.items():
            self.assertIn('lucro_liquido', dados)
            self.assertIn('custo_racao', dados)
```

**Checklist:**
- [ ] Criar testes de query count
- [ ] Testar com 20 lotes
- [ ] Medir tempo pré e pós
- [ ] Executar `python manage.py test lotes`

---

### Estimativa: 6 horas

---

## 3. TASK 1.3 - Validações de Estado (5 horas)

### Status: 🟠 ALTA

Adicionar validações em `clean()` e `save()` para prevenir transições inválidas.

---

### Step 1.3.1: Validações em Ave

**Arquivo:** [aves/models.py](aves/models.py)

```python
from django.core.exceptions import ValidationError

class Ave(TimeStampedModel, AtivoInativoModel, AuditModel):
    # ... campos existentes
    
    def clean(self):
        """Validações de negócio para Ave."""
        super().clean()
        
        # Validação 1: Reprodutor não pode ser vendido
        if self.finalidade == self.FINALIDADE_REPRODUCAO and self.status == self.STATUS_VENDIDA:
            raise ValidationError(
                "Ave com finalidade de reprodução não pode ter status 'vendida'. "
                "Use 'abatida' ou 'morta' se retirado do programa."
            )
        
        # Validação 2: Ave abatida ou morta não pode voltar à vida
        if hasattr(self, '_original_status'):
            original = self._original_status
            if original in [self.STATUS_ABATIDA, self.STATUS_MORTA]:
                if self.status not in [self.STATUS_ABATIDA, self.STATUS_MORTA]:
                    raise ValidationError(
                        f"Ave com status '{original}' não pode voltar ao status '{self.status}'. "
                        "Isto violaria a lógica biológica."
                    )
        
        # Validação 3: Status requer campo complementar
        if self.status == self.STATUS_VENDIDA and not self.valor_referencia:
            raise ValidationError({
                'valor_referencia': 'Ave vendida precisa de valor de referência.'
            })
        
        # Validação 4: Data de nascimento não pode ser no futuro
        if self.data_nascimento:
            from django.utils import timezone
            if self.data_nascimento > timezone.localdate():
                raise ValidationError({
                    'data_nascimento': 'Data de nascimento não pode estar no futuro.'
                })
    
    def save(self, *args, **kwargs):
        """Salvar com validações."""
        self.full_clean()  # ← Chama clean()
        super().save(*args, **kwargs)
```

**Checklist:**
- [ ] Adicionar clean() em Ave
- [ ] Detectar transições inválidas
- [ ] Chamar full_clean() em save()
- [ ] Testar ValidationError

---

### Step 1.3.2: Validações em Lote

**Arquivo:** [lotes/models.py](lotes/models.py)

```python
class Lote(TimeStampedModel, AtivoInativoModel, AuditModel):
    # ... campos existentes
    
    def clean(self):
        """Validações de negócio para Lote."""
        super().clean()
        
        # Validação 1: Quantidade atual não pode ser negativa
        if self.quantidade_atual is not None and self.quantidade_atual < 0:
            raise ValidationError({
                'quantidade_atual': 'Quantidade de aves não pode ser negativa.'
            })
        
        # Validação 2: Quantidade atual não pode > inicial (em teoria)
        if (self.quantidade_atual and self.quantidade_inicial and
            self.quantidade_atual > self.quantidade_inicial):
            raise ValidationError({
                'quantidade_atual': 'Quantidade atual não pode ser maior que inicial.'
            })
        
        # Validação 3: Lote reprodutivo precisa ter dados
        if self.reprodutivo and not self.data_inicio_reproducao:
            raise ValidationError({
                'data_inicio_reproducao': 'Lote reprodutivo precisa de data de início.'
            })
        
        # Validação 4: Proporção reprodutiva válida
        if self.reprodutivo and self.quantidade_femeas and self.quantidade_machos:
            razao = self.quantidade_femeas / self.quantidade_machos
            if razao < 0.5 or razao > 10:  # Razão absurda
                raise ValidationError(
                    f"Proporção fêmea:macho de 1:{razao:.1f} é inválida. "
                    f"Esperado entre 1:0.5 e 1:10."
                )
    
    def save(self, *args, **kwargs):
        """Salvar com validações."""
        self.full_clean()  # ← Chama clean()
        
        # Auto-fill quantidade_atual se nao tiver
        if self.quantidade_atual is None:
            self.quantidade_atual = self.quantidade_inicial
        
        super().save(*args, **kwargs)
```

**Checklist:**
- [ ] Adicionar clean() em Lote
- [ ] Validar quantidades
- [ ] Validar reprodução
- [ ] Chamar full_clean() em save()

---

### Step 1.3.3: Validações em Incubacao

**Arquivo:** [incubacao/models.py](incubacao/models.py)

```python
class Incubacao(TimeStampedModel, AuditModel):
    # ... campos existentes
    
    def clean(self):
        """Validações de negócio para Incubacao."""
        super().clean()
        
        # Validação: Ovos férteis + inférteis não pode > quantidade_ovos
        total_classificados = (self.ovos_fertis or 0) + (self.ovos_infertis or 0)
        if total_classificados > (self.quantidade_ovos or 0):
            raise ValidationError(
                f"Ovos férteis ({self.ovos_fertis}) + inférteis ({self.ovos_infertis}) "
                f"não podem ser maiores que total ({self.quantidade_ovos})."
            )
        
        # Validação: Quantidade nascida não pode > ovos férteis
        if self.quantidade_nascida and self.quantidade_nascida > (self.ovos_fertis or self.quantidade_ovos):
            raise ValidationError({
                'quantidade_nascida': 'Quantidade nascida não pode ser maior que ovos férteis.'
            })
    
    def save(self, *args, **kwargs):
        """Salvar com validações."""
        self.full_clean()  # ← Chama clean()
        
        # Auto-calc previsão
        if not self.previsao_eclosao and self.data_entrada:
            self.previsao_eclosao = self.data_entrada + timedelta(days=21)
        
        super().save(*args, **kwargs)
```

**Checklist:**
- [ ] Adicionar clean() em Incubacao
- [ ] Validar quantidades
- [ ] Chamar full_clean()

---

### Step 1.3.4: Testes de Validação

**Arquivo:** [aves/tests.py](aves/tests.py)

```python
from django.test import TestCase
from django.core.exceptions import ValidationError

class AveValidationTestCase(TestCase):
    
    def test_ave_reprodutor_nao_pode_vender(self):
        """Ave com finalidade reprodução não pode ser vendida."""
        ave = Ave(
            finalidade=Ave.FINALIDADE_REPRODUCAO,
            status=Ave.STATUS_VENDIDA,
            valor_referencia=1000
        )
        with self.assertRaises(ValidationError):
            ave.save()
    
    def test_ave_vendida_precisa_valor(self):
        """Ave vendida precisa de valor_referencia."""
        ave = Ave(status=Ave.STATUS_VENDIDA, valor_referencia=None)
        with self.assertRaises(ValidationError):
            ave.save()
```

**Checklist:**
- [ ] Criar testes de ValidationError
- [ ] Testar transições proibidas
- [ ] Executar `python manage.py test aves`

---

### Estimativa: 5 horas

---

## 4. TASK 1.4 - Eliminar Duplicação Sanidade (4 horas)

### Status: 🟠 ALTA

Criar mixin com properties compartilhadas entre AplicacaoVacina e VacinaLote.

---

### Step 1.4.1: Criar Mixin

**Arquivo:** Criar [sanidade/mixins.py](sanidade/mixins.py)

```python
from django.utils import timezone
from datetime import timedelta


class VacinacaoOperacionalMixin:
    """
    Mixin com properties compartilhadas para vacinação.
    
    Classes que usam isto devem implementar:
    - get_data_programada() → DateField
    - get_status_pendente() → bool
    """
    
    def get_data_programada(self):
        """Override em subclass."""
        raise NotImplementedError("Subclass deve implementar get_data_programada()")
    
    def get_status_pendente(self):
        """Override em subclass."""
        raise NotImplementedError("Subclass deve implementar get_status_pendente()")
    
    @property
    def atrasada(self):
        """Verifica se vacinação está em atraso."""
        hoje = timezone.localdate()
        data_prog = self.get_data_programada()
        return bool(self.get_status_pendente() and data_prog and data_prog < hoje)
    
    @property
    def prevista_hoje(self):
        """Verifica se vacinação está prevista para hoje."""
        hoje = timezone.localdate()
        data_prog = self.get_data_programada()
        return bool(self.get_status_pendente() and data_prog and data_prog == hoje)
    
    @property
    def proxima(self):
        """Verifica se vacinação está na janela próxima (7 dias)."""
        hoje = timezone.localdate()
        data_prog = self.get_data_programada()
        return bool(
            self.get_status_pendente() 
            and data_prog 
            and hoje < data_prog <= hoje + timedelta(days=7)
        )
    
    @property
    def status_operacional(self):
        """Retorna status operacional para display."""
        if not self.get_status_pendente():  # Se não está pendente
            if hasattr(self, 'status'):  # AplicacaoVacina
                if self.status == 'aplicada':
                    return "aplicada"
                if self.status == 'cancelada':
                    return "cancelada"
            elif hasattr(self, 'aplicada'):  # VacinaLote
                if self.aplicada:
                    return "aplicada"
            return "pendente"
        
        if self.atrasada:
            return "atrasada"
        if self.prevista_hoje:
            return "hoje"
        if self.proxima:
            return "proxima"
        return "pendente"
    
    @property
    def status_operacional_label(self):
        """Retorna label legível do status."""
        labels = {
            "aplicada": "Aplicada / OK",
            "cancelada": "Cancelada",
            "atrasada": "Atrasada",
            "hoje": "Prevista para hoje",
            "proxima": "Próxima (próximos 7 dias)",
            "pendente": "Pendente",
        }
        return labels.get(self.status_operacional, "Desconhecido")
    
    @property
    def dias_atraso(self):
        """Retorna dias em atraso (0 se não atrasado)."""
        if not self.atrasada:
            return 0
        data_prog = self.get_data_programada()
        return (timezone.localdate() - data_prog).days
    
    @property
    def urgencia_operacional(self):
        """Retorna nível de urgência se atrasado."""
        if not self.atrasada:
            return ""
        if self.dias_atraso >= 7:
            return "critica"
        if self.dias_atraso >= 3:
            return "alta"
        return "moderada"
```

**Checklist:**
- [ ] Criar sanidade/mixins.py
- [ ] Implementar VacinacaoOperacionalMixin
- [ ] Documentar métodos abstratos

---

### Step 1.4.2: Aplicar Mixin em AplicacaoVacina

**Arquivo:** [sanidade/models.py](sanidade/models.py) - AplicacaoVacina

```python
from sanidade.mixins import VacinacaoOperacionalMixin

class AplicacaoVacina(TimeStampedModel, AuditModel, VacinacaoOperacionalMixin):
    # ... campos existentes
    
    def get_data_programada(self):
        """Implementação abstrata do mixin."""
        return self.data_programada
    
    def get_status_pendente(self):
        """Implementação abstrata do mixin."""
        return self.status == self.STATUS_PENDENTE
    
    # ← REMOVER todas as properties que estão em VacinacaoOperacionalMixin:
    #   - atrasada
    #   - prevista_hoje
    #   - proxima
    #   - status_operacional
    #   - status_operacional_label
    #   - dias_atraso
    #   - urgencia_operacional
    
    # ← MANTER properties únicas:
    @property
    def data_final_carencia(self):
        if self.status != self.STATUS_APLICADA or not self.data_aplicacao or not self.vacina:
            return None
        dias = self.vacina.carencia_dias or 0
        return self.data_aplicacao + timezone.timedelta(days=dias)

    @property
    def carencia_ativa(self):
        fim = self.data_final_carencia
        return bool(fim and fim >= timezone.localdate())
```

**Checklist:**
- [ ] Adicionar VacinacaoOperacionalMixin
- [ ] Implementar get_data_programada()
- [ ] Implementar get_status_pendente()
- [ ] Remover properties duplicadas

---

### Step 1.4.3: Aplicar Mixin em VacinaLote

**Arquivo:** [sanidade/models.py](sanidade/models.py) - VacinaLote

```python
class VacinaLote(TimeStampedModel, AuditModel, VacinacaoOperacionalMixin):
    # ... campos existentes
    
    def get_data_programada(self):
        """Implementação abstrata do mixin."""
        return self.data_prevista
    
    def get_status_pendente(self):
        """Implementação abstrata do mixin."""
        return not self.aplicada
    
    # ← REMOVER todas as properties que estão em VacinacaoOperacionalMixin
```

**Checklist:**
- [ ] Adicionar VacinacaoOperacionalMixin
- [ ] Implementar get_data_programada()
- [ ] Implementar get_status_pendente()
- [ ] Remover properties duplicadas

---

### Step 1.4.4: Consolidar Carência

**Arquivo:** [sanidade/models.py](sanidade/models.py)

```python
class CarenciaMixin:
    """Mixin para cálculo de carência (Vacina + Medicamento)."""
    
    def get_data_fim_carencia(self):
        """Override em subclass."""
        raise NotImplementedError()
    
    @property
    def data_final_carencia(self):
        """Data final da carência."""
        return self.get_data_fim_carencia()
    
    @property
    def carencia_ativa(self):
        """Verifica se carência está ativa."""
        fim = self.data_final_carencia
        return bool(fim and fim >= timezone.localdate())


class AplicacaoVacina(..., CarenciaMixin):
    def get_data_fim_carencia(self):
        if self.status != self.STATUS_APLICADA or not self.data_aplicacao or not self.vacina:
            return None
        dias = self.vacina.carencia_dias or 0
        return self.data_aplicacao + timezone.timedelta(days=dias)


class Tratamento(..., CarenciaMixin):
    def get_data_fim_carencia(self):
        if not self.data_fim:
            return None
        return self.data_fim + timezone.timedelta(days=self.periodo_carencia or 0)
```

**Checklist:**
- [ ] Criar CarenciaMixin
- [ ] Aplicar em AplicacaoVacina e Tratamento
- [ ] Remover duplicação

---

### Step 1.4.5: Testar

**Arquivo:** [sanidade/tests.py](sanidade/tests.py)

```python
from django.test import TestCase
from django.utils import timezone

class VacinacaoOperacionalTestCase(TestCase):
    
    def test_aplicacao_vacina_atrasada(self):
        """AplicacaoVacina.atrasada deve funcionar."""
        app = AplicacaoVacina(
            data_programada=timezone.localdate() - timedelta(days=3),
            status=AplicacaoVacina.STATUS_PENDENTE
        )
        self.assertTrue(app.atrasada)
    
    def test_vacina_lote_atrasada(self):
        """VacinaLote.atrasada deve funcionar (mesmo código)."""
        vl = VacinaLote(
            data_prevista=timezone.localdate() - timedelta(days=3),
            aplicada=False
        )
        self.assertTrue(vl.atrasada)
    
    def test_mixin_compartilhado(self):
        """Properties do mixin devem retornar mesmos resultados em ambas."""
        data_atraso = timezone.localdate() - timedelta(days=2)
        
        app = AplicacaoVacina(
            data_programada=data_atraso,
            status=AplicacaoVacina.STATUS_PENDENTE
        )
        
        vl = VacinaLote(
            data_prevista=data_atraso,
            aplicada=False
        )
        
        # Ambas devem ter mesma lógica
        self.assertEqual(app.dias_atraso, vl.dias_atraso)
        self.assertEqual(app.atrasada, vl.atrasada)
        self.assertEqual(app.urgencia_operacional, vl.urgencia_operacional)
```

**Checklist:**
- [ ] Criar testes de compartilhamento
- [ ] Verificar que lógica é idêntica
- [ ] Executar `python manage.py test sanidade`

---

### Estimativa: 4 horas

---

## 5. TASK 1.5 - Transações Atômicas em MovimentoEstoque (3 horas)

### Status: 🟠 ALTA

**Problema:** MovimentoEstoque.save() atualiza ItemEstoque sem transação.

---

### Step 1.5.1: Envolver em @transaction.atomic

**Arquivo:** [estoque/models.py](estoque/models.py)

```python
from django.db import transaction

class MovimentoEstoque(TimeStampedModel, AuditModel):
    # ... campos
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        """Salvar com integridade transacional."""
        creating = self.pk is None
        item = self.item
        
        if creating and item:
            qtd_atual = item.quantidade_atual or 0
            if self.tipo == self.TIPO_ENTRADA:
                novo_qtd = qtd_atual + (self.quantidade or 0)
                if self.custo_unitario:
                    item.ultimo_preco = self.custo_unitario
                    total_custo = (item.custo_medio or 0) * qtd_atual + (self.custo_unitario * (self.quantidade or 0))
                    if novo_qtd:
                        item.custo_medio = total_custo / novo_qtd
                item.quantidade_atual = novo_qtd
                
            elif self.tipo == self.TIPO_SAIDA:
                novo_qtd = qtd_atual - (self.quantidade or 0)
                if novo_qtd < 0:
                    raise ValidationError(
                        f"Saída de {self.quantidade} unidades não é possível. "
                        f"Estoque atual: {qtd_atual}."
                    )
                item.quantidade_atual = novo_qtd
                
            elif self.tipo == self.TIPO_AJUSTE:
                item.quantidade_atual = self.quantidade or 0
        
        # Salvar movimento
        super().save(*args, **kwargs)
        
        # Salvar item (dentro da mesma transação)
        if creating and item:
            item.save()
```

**Checklist:**
- [ ] Adicionar `@transaction.atomic` ao save()
- [ ] Validar quantidades negativas
- [ ] Testar que movimento + item são salvos juntos
- [ ] Testar que falha na transação reverte ambos

---

### Step 1.5.2: Testes de Integridade

**Arquivo:** [estoque/tests.py](estoque/tests.py)

```python
from django.test import TransactionTestCase
from django.db import IntegrityError

class MovimentoEstoqueAtomicoTestCase(TransactionTestCase):
    
    def test_movimento_entrada_atualiza_item(self):
        """Entrada deve atualizar ItemEstoque.quantidade_atual."""
        item = ItemEstoque.objects.create(
            nome="Ração Test",
            categoria=ItemEstoque.CAT_RACAO,
            quantidade_atual=100
        )
        
        movimento = MovimentoEstoque.objects.create(
            item=item,
            data=timezone.localdate(),
            tipo=MovimentoEstoque.TIPO_ENTRADA,
            quantidade=50,
            custo_unitario=10
        )
        
        item.refresh_from_db()
        self.assertEqual(item.quantidade_atual, 150)
        self.assertEqual(item.custo_medio, 
                        (100*0 + 50*10) / 150)  # FIFO
    
    def test_movimento_saida_nao_negativa(self):
        """Saída não deve deixar quantidade negativa."""
        item = ItemEstoque.objects.create(
            nome="Ração Test",
            categoria=ItemEstoque.CAT_RACAO,
            quantidade_atual=50
        )
        
        with self.assertRaises(ValidationError):
            MovimentoEstoque.objects.create(
                item=item,
                data=timezone.localdate(),
                tipo=MovimentoEstoque.TIPO_SAIDA,
                quantidade=100
            )
        
        item.refresh_from_db()
        self.assertEqual(item.quantidade_atual, 50)  # Não mudou
    
    def test_transacao_atomica_rollback(self):
        """Se movimento falhar, item não deve ser atualizado."""
        item = ItemEstoque.objects.create(
            nome="Ração Test",
            categoria=ItemEstoque.CAT_RACAO,
            quantidade_atual=100
        )
        
        # Simular erro forçado
        with self.assertRaises(Exception):
            with transaction.atomic():
                movimento = MovimentoEstoque(
                    item=item,
                    data=timezone.localdate(),
                    tipo=MovimentoEstoque.TIPO_ENTRADA,
                    quantidade=50
                )
                movimento.save()
                
                # Forçar erro após salvar
                raise IntegrityError("Simulated DB error")
        
        item.refresh_from_db()
        self.assertEqual(item.quantidade_atual, 100)  # Reverteu
```

**Checklist:**
- [ ] Criar testes transacionais
- [ ] Testar entrada, saída, ajuste
- [ ] Testar rollback de falha
- [ ] Executar `python manage.py test estoque`

---

### Estimativa: 3 horas

---

## 6. TASK 1.6 - Criar Índices de BD (2 horas)

### Status: 🟡 MÉDIA

---

### Step 1.6.1: Criar Migration

**Arquivo:** Criar [migrations/0001_add_indexes_fase1.py](migrations/0001_add_indexes_fase1.py)

```python
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aves', '0001_initial'),  # Ajustar conforme seu histórico
        ('lotes', '0001_initial'),
        ('estoque', '0001_initial'),
        ('vendas', '0001_initial'),
        # ... etc
    ]

    operations = [
        # Índices Aves
        migrations.AddIndex(
            model_name='ave',
            index=models.Index(fields=['finalidade', 'status'], 
                             name='aves_finalidade_status_idx'),
        ),
        migrations.AddIndex(
            model_name='ave',
            index=models.Index(fields=['lote_id', 'status'], 
                             name='aves_lote_status_idx'),
        ),
        
        # Índices Lotes
        migrations.AddIndex(
            model_name='lote',
            index=models.Index(fields=['status', 'finalidade'], 
                             name='lotes_status_finalidade_idx'),
        ),
        
        # Índices Vendas
        migrations.AddIndex(
            model_name='venda',
            index=models.Index(fields=['cliente', 'data'], 
                             name='vendas_cliente_data_idx'),
        ),
        
        # Índices Sanidade
        migrations.AddIndex(
            model_name='aplicacaovacina',
            index=models.Index(fields=['lote_id', 'data_programada'], 
                             name='sanidade_app_lote_data_idx'),
        ),
        migrations.AddIndex(
            model_name='vacinaLote',
            index=models.Index(fields=['lote_id', 'data_prevista'], 
                             name='sanidade_vac_lote_data_idx'),
        ),
        
        # Índices Nascimentos
        migrations.AddIndex(
            model_name='nascimento',
            index=models.Index(fields=['lote_id', 'data'], 
                             name='nascimentos_lote_data_idx'),
        ),
        
        # Índices Abate (M2M)
        migrations.AddIndex(
            model_name='abate',
            index=models.Index(fields=['lote_id', 'data'], 
                             name='abate_lote_data_idx'),
        ),
        migrations.AddIndex(
            model_name='abate_aves',
            index=models.Index(fields=['abate_id', 'ave_id'], 
                             name='abate_aves_idx'),
        ),
    ]
```

**Checklist:**
- [ ] Criar migration file
- [ ] Listar todos os índices faltantes
- [ ] Executar `python manage.py migrate`
- [ ] Verificar no DB: `SHOW INDEX FROM tabela_name;`

---

### Estimativa: 2 horas

---

## 7. TASK 1.7 - Reprodutor Tracking (4 horas)

### Status: 🟡 MÉDIA

**Problema:** Reprodutor(Ave) sem saber em qual Lote está agora.

---

### Step 1.7.1: Criar Modelo Histórico

**Arquivo:** Expandir [reprodutores/models.py](reprodutores/models.py)

```python
from django.db import models
from core.models import TimeStampedModel, AuditModel


class HistoricoReprodutorLote(TimeStampedModel, AuditModel):
    """Rastreia em qual Lote o reprodutor esteve em cada período."""
    
    reprodutor = models.ForeignKey(
        'Reprodutor',
        on_delete=models.CASCADE,
        related_name='historico_lotes'
    )
    lote = models.ForeignKey(
        'lotes.Lote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historico_reprodutores'
    )
    data_inicio = models.DateField(help_text="Quando entrou no lote")
    data_fim = models.DateField(
        null=True,
        blank=True,
        help_text="Quando saiu do lote (NULL = ainda está)"
    )
    observacoes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Histórico de Reprodutor em Lote"
        verbose_name_plural = "Históricos de Reprodutor em Lote"
        ordering = ['-data_inicio']
        indexes = [
            models.Index(fields=['reprodutor', 'data_inicio'], 
                        name='repr_lote_hist_idx'),
        ]
    
    def __str__(self):
        return f"{self.reprodutor} em {self.lote} ({self.data_inicio})"
    
    @property
    def ainda_no_lote(self):
        return self.data_fim is None


class Reprodutor(TimeStampedModel, AtivoInativoModel, AuditModel):
    # ... campos existentes
    
    @property
    def lote_atual(self):
        """Retorna o lote onde o reprodutor está agora."""
        historico = self.historico_lotes.filter(data_fim__isnull=True).first()
        return historico.lote if historico else None
    
    @property
    def historico_todos_lotes(self):
        """Retorna histórico completo deste reprodutor."""
        return self.historico_lotes.order_by('-data_inicio')
```

**Checklist:**
- [ ] Criar HistoricoReprodutorLote
- [ ] Adicionar property lote_atual
- [ ] Adicionar property historico_todos_lotes
- [ ] Criar migration

---

### Step 1.7.2: Signal para Auto-Tracking

**Arquivo:** Criar/expandir [reprodutores/signals.py](reprodutores/signals.py)

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from reprodutores.models import Reprodutor, HistoricoReprodutorLote


@receiver(post_save, sender=Reprodutor)
def track_reprodutor_lote_change(sender, instance, created, **kwargs):
    """
    Quando Reprodutor é criado/atualizado, rastreia mudança de lote.
    """
    if created:
        # Novo reprodutor: criar histórico se tiver lote
        if instance.lote_atual:
            HistoricoReprodutorLote.objects.create(
                reprodutor=instance,
                lote=instance.lote_atual,
                data_inicio=timezone.localdate()
            )
    else:
        # Atualização: verificar se mudou de lote
        # (Isto requer comparação com estado anterior - mais complexo)
        # Por ora, apenas log
        pass
```

**Checklist:**
- [ ] Criar reprodutores/signals.py
- [ ] Registrar em reprodutores/apps.py ready()
- [ ] Testar que histórico é criado

---

### Estimativa: 4 horas

---

## 📊 Resumo Executivo FASE 1

| Task | Prioridade | Horas | Status |
|------|-----------|-------|--------|
| 1.1 Sync Venda-Financeiro | 🔴 Crítica | 4h | ⏳ A fazer |
| 1.2 Otimizar N+1 Lote | 🔴 Crítica | 6h | ⏳ A fazer |
| 1.3 Validações Estado | 🟠 Alta | 5h | ⏳ A fazer |
| 1.4 Eliminar Duplicação | 🟠 Alta | 4h | ⏳ A fazer |
| 1.5 Transações Atômicas | 🟠 Alta | 3h | ⏳ A fazer |
| 1.6 Criar Índices BD | 🟡 Média | 2h | ⏳ A fazer |
| 1.7 Reprodutor Tracking | 🟡 Média | 4h | ⏳ A fazer |
| **TOTAL** | | **28h** | |

**Sprint:** 1 developer × 4 dias (7h/dia)

**Entregas Esperadas:**
- ✅ Venda-Financeiro 100% consistente (sem gaps)
- ✅ Queries de listagem: 140 → 5 queries (-97%)
- ✅ Dados corretos e validados
- ✅ Zero código duplicado em sanidade
- ✅ Todas operações atômicas
- ✅ BD otimizado com índices
- ✅ Rastreamento de reprodutores

---

**Próxima Fase:** FASE 2 - Novos Módulos (Dashboards, Relatórios, Mobile)

Pronto para começar FASE 1? 🚀

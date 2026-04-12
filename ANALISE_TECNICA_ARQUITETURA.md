# Análise Técnica Completa - Sistema SISMGC Django
**Data:** 12 de abril de 2026  
**Escopo:** Arquitetura, Models, Views, Integrações e Problemas Estruturais

---

## 1. MAPA DE RELACIONAMENTOS (DEPENDÊNCIAS E FOREIGN KEYS)

### 1.1 Núcleo de Aves e Genética

```
Ave (aves/models.py)
├─ ForeignKey → Linhagem (linhagens/models.py) [PROTECT]
├─ ForeignKey → self (pai) [SET_NULL]
├─ ForeignKey → self (mae) [SET_NULL]
├─ ForeignKey → Lote (lote_atual) [SET_NULL]
└─ Reverse:
   ├─ filhos_pai ← Ave
   ├─ filhos_mae ← Ave
   ├─ incubacoes_matriz ← Incubacao
   ├─ vendas ← Venda
   ├─ abates ← Abate (M2M)
   ├─ lancamentos ← LancamentoFinanceiro
   ├─ vacinas ← AplicacaoVacina
   ├─ tratamentos ← Tratamento
   ├─ registros_como_pai ← RegistroGenetico
   ├─ registros_como_mae ← RegistroGenetico
   └─ registro_genetico ← RegistroGenetico

Linhagem (linhagens/models.py)
├─ Reverse:
   ├─ aves ← Ave
   ├─ lotes ← Lote
   └─ nascimentos ← Nascimento

RegistroGenetico (genetica/models.py)
├─ ForeignKey → Ave (pai) [SET_NULL] → registros_como_pai
├─ ForeignKey → Ave (mae) [SET_NULL] → registros_como_mae
├─ ForeignKey → Ave (filho) [CASCADE] → registro_genetico
└─ unique_together: (pai, mae, filho)

Reprodutor (reprodutores/models.py)
├─ OneToOneField → Ave [CASCADE] → reprodutor
├─ TIPO: matriz/reprodutor (validado em save())
├─ Status: ativo/descanso/vendido/descartado
└─ Qualidade genética: padrão/superior/pura
```

### 1.2 Lotes (Núcleo Operacional)

```
Lote (lotes/models.py)
├─ ForeignKey → Linhagem (linhagem_principal) [PROTECT]
├─ Reverse:
│  ├─ aves ← Ave
│  ├─ vendas ← Venda
│  ├─ abates ← Abate
│  ├─ incubacoes ← Incubacao
│  ├─ nascimentos ← Nascimento
│  ├─ lancamentos ← LancamentoFinanceiro
│  ├─ movimentoestoque_set ← MovimentoEstoque (reverse implicit)
│  ├─ vacinas ← AplicacaoVacina
│  ├─ vacinas_lote ← VacinaLote
│  └─ tratamentos ← Tratamento
└─ Properties (CRÍTICO - Fazem queries):
   ├─ custo_por_ave: Calcula de custo_acumulado
   ├─ custo_racao: Query (MovimentoEstoque → ItemEstoque)
   ├─ despesas_extras: Query (LancamentoFinanceiro)
   ├─ receita_vendas: Query (Venda)
   ├─ custo_sanitario: Query (LancamentoFinanceiro)
   ├─ lucro_final: usa 3 properties acima (cascata!)
   ├─ mortalidade_percentual: Cálculo
   ├─ consumo_racao_total: Query (MovimentoEstoque → ItemEstoque)
   ├─ conversao_alimentar: usa consumo_racao_total
   ├─ proporcao_reprodutiva: Cálculo
   └─ resumo_incubacao: Query (Incubacao + Nascimento)
```

### 1.3 Vendas e Financeiro (INTEGRAÇÃO CRÍTICA)

```
Venda (vendas/models.py)
├─ ForeignKey → Lote (lote) [SET_NULL]
├─ ForeignKey → Ave (ave) [SET_NULL]
├─ OneToOneField → LancamentoFinanceiro (lancamento_financeiro) [SET_NULL]
│  └─ PROBLEMA: Relacionamento reverso = venda
└─ Properties:
   ├─ tem_entrada_financeira: Verifica hasattr(lancamento_financeiro)
   ├─ status_integracao: 'vinculada', 'pendente_vínculo', 'não_sincronizada'
   └─ get_status_integracao_display(): Label legível

LancamentoFinanceiro (financeiro/models.py)
├─ ForeignKey → Lote (lote) [SET_NULL]
├─ ForeignKey → Ave (ave) [SET_NULL]
├─ OneToOneField → Venda (venda) [SET_NULL]
│  └─ reverse = lancamento_financeiro
└─ Campos:
   ├─ tipo: entrada/saida
   ├─ categoria: racao/vacinas/medicamentos/energia/transporte/manutencao/mao_obra/equipamentos/vendas/outros
   ├─ data, descricao, valor
   └─ forma_pagamento

Sincronização Venda ↔ Financeiro
├─ Função: _sync_venda_financeiro(venda) [vendas/views.py]
├─ Regras:
│  ├─ Status PAGO → Cria/atualiza LancamentoFinanceiro (ENTRADA)
│  ├─ Status NÃO PAGO → Deleta LancamentoFinanceiro se existir
│  └─ OneToOneField previne duplicidade
├─ Chamada em:
│  ├─ VendaCreateView.form_valid()
│  ├─ VendaUpdateView.form_valid()
│  └─ VendaDeleteView.delete()
└─ PROBLEMA: NÃO é automático, depende de chamar função na view
```

### 1.4 Estoque (Inventário e Movimentação)

```
ItemEstoque (estoque/models.py)
├─ Categorias: racao/graos/vacina/medicamento/material/outros
├─ Unidades: kg/g/un/ml/L/ovos
├─ Campos:
│  ├─ quantidade_atual: Atualizada por MovimentoEstoque.save()
│  ├─ custo_unitario, custo_medio, ultimo_preco
│  ├─ estoque_minimo
│  ├─ validade
│  └─ fornecedor, localizacao
├─ Properties:
│  ├─ estoque_baixo: quantidade_atual <= estoque_minimo
│  ├─ vencido: validade < hoje
│  └─ vencendo: validade em 30 dias
└─ Reverse:
   └─ movimentacoes ← MovimentoEstoque

MovimentoEstoque (estoque/models.py)
├─ ForeignKey → ItemEstoque [CASCADE] → movimentacoes
├─ ForeignKey → Lote (lote_relacionado) [SET_NULL]
├─ Tipos: entrada/saida/ajuste
├─ Motivos: compra/consumo/descarte/ajuste/uso_sanitario/uso_lote
├─ save() Override: CRÍTICO!
│  ├─ Atualiza ItemEstoque.quantidade_atual
│  ├─ Recalcula custo_medio em entrada
│  └─ SEM TRANSAÇÃO ATÔMICA = RISCO!
└─ Campos:
   ├─ data, quantidade, custo_unitario
   └─ fornecedor, observacoes
```

### 1.5 Incubação e Nascimento

```
Incubacao (incubacao/models.py)
├─ ForeignKey → Ave (matriz_responsavel) [SET_NULL]
├─ ForeignKey → Lote (lote_relacionado) [SET_NULL]
├─ Campos:
│  ├─ tipo: chocadeira/natural
│  ├─ quantidade_ovos, ovos_fertis, ovos_infertis, perdas
│  ├─ data_entrada, previsao_eclosao (auto-calculated: +21 dias)
│  ├─ data_eclosao, quantidade_nascida
│  └─ status: andamento/concluida/cancelada
├─ Reverse:
│  └─ nascimentos ← Nascimento [CASCADE]
└─ Properties:
   ├─ taxa_fertilidade: ovos_fertis / quantidade_ovos
   ├─ taxa_eclosao: quantidade_nascida / ovos_fertis
   └─ taxa_perda: perdas / quantidade_ovos

Nascimento (nascimentos/models.py)
├─ ForeignKey → Incubacao [CASCADE] → nascimentos
├─ ForeignKey → Linhagem [PROTECT]
├─ ForeignKey → Lote (lote_destino) [PROTECT]
├─ Campos:
│  ├─ data, quantidade_nascida, quantidade_viva, quantidade_morta
│  └─ observacoes
├─ save() Override: CONFUSO!
│  ├─ Recalcula quantidade_nascida se for 0
│  ├─ Valida: viva + morta <= nascida
│  ├─ Se viva + morta exato, preenche morta automaticamente
│  └─ Múltiplas operações sem clareza
└─ Vínculo com Lote.resumo_incubacao (property que agrega)
```

### 1.6 Sanidade (Vacinação e Saúde)

```
Vacina (sanidade/models.py)
├─ Campos: nome, fabricante, dose_recomendada, carencia_dias
├─ Reverse:
│  └─ aplicacoes ← AplicacaoVacina [CASCADE]

AplicacaoVacina (sanidade/models.py)
├─ ForeignKey → Vacina [CASCADE] → aplicacoes
├─ ForeignKey → Ave (ave) [SET_NULL]
├─ ForeignKey → Lote (lote) [SET_NULL]
├─ Campos:
│  ├─ data_programada, data_aplicacao
│  ├─ dose, status: pendente/aplicada/cancelada
│  └─ observacoes
├─ Properties: REPETIDAS EM VacinaLote (DUPLICAÇÃO!)
│  ├─ data_final_carencia
│  ├─ carencia_ativa
│  ├─ atrasada: status=PENDENTE e data < hoje
│  ├─ prevista_hoje
│  ├─ proxima: janela 7 dias
│  ├─ status_operacional: aplicada/cancelada/atrasada/hoje/proxima/pendente
│  ├─ status_operacional_label
│  ├─ dias_atraso
│  └─ urgencia_operacional: critica/alta/moderada

Medicamento (sanidade/models.py)
├─ Campos: nome, categoria, validade
├─ Reverse:
│  └─ tratamentos ← Tratamento [CASCADE]

Tratamento (sanidade/models.py)
├─ ForeignKey → Medicamento [PROTECT] → tratamentos
├─ ForeignKey → Ave (ave) [SET_NULL]
├─ ForeignKey → Lote (lote) [SET_NULL]
├─ Campos:
│  ├─ doenca, data_inicio, data_fim, periodo_carencia
│  └─ observacoes
├─ Properties:
│  ├─ data_final_carencia
│  ├─ carencia_ativa
│  └─ em_andamento: data_fim null ou > hoje

VacinaLote (sanidade/models.py)
├─ ForeignKey → Lote [CASCADE] → vacinas_lote
├─ Campos:
│  ├─ nome_vacina, data_prevista
│  ├─ aplicada: bool, data_aplicacao
│  └─ unique_together: (lote, nome_vacina, data_prevista)
└─ Properties: DUPLICADAS DE AplicacaoVacina!
   ├─ atrasada, prevista_hoje, proxima, status_operacional, etc
   └─ MESMO CÓDIGO em ambas as classes!
```

### 1.7 Histórico e Auditoria

```
HistoricoEvento (historico/models.py)
├─ Campos:
│  ├─ entidade: string (ex: "Ave", "Lote", "Venda")
│  ├─ referencia_id: PositiveIntegerField (pk da entidade)
│  ├─ acao: create/update/delete/status
│  ├─ descricao, detalhes (JSONField)
│  └─ usuario: ForeignKey → User [SET_NULL]
├─ Signals (historico/signals.py) que disparam:
│  ├─ @receiver(post_save, handler=historico_ave) → Ave
│  ├─ @receiver(post_save, handler=historico_lote) → Lote
│  ├─ @receiver(post_save, handler=historico_venda) → Venda
│  ├─ @receiver(post_save, handler=historico_abate) → Abate
│  ├─ @receiver(post_save, handler=historico_vacina) → AplicacaoVacina
│  ├─ @receiver(post_save, handler=historico_tratamento) → Tratamento
│  └─ @receiver(post_save, handler=historico_estoque) → MovimentoEstoque
└─ Problema: Logging simples, sem rastreamento de mudanças específicas
```

### 1.8 Abate (Processamento)

```
Abate (abate/models.py)
├─ ForeignKey → Lote [SET_NULL]
├─ ManyToManyField → Ave (aves) [blank=True]
│  └─ PROBLEMA: M2M sem índices, sem related_name explícito
├─ Campos:
│  ├─ data, quantidade_abatida
│  ├─ peso_total, peso_medio (auto-calculated)
│  ├─ custo_acumulado, receita_gerada
│  └─ destino, observacoes
└─ Property:
   └─ lucro_prejuizo: receita - custo
```

### 1.9 Orçamento Futuro

```
OrcamentoFuturo (financeiro/models.py)
├─ Campos:
│  ├─ titulo, descricao, categoria
│  ├─ valor_previsto, valor_ja_reservado
│  ├─ status: planejado/andamento/concluido/cancelado
│  ├─ prioridade: baixa/media/alta
│  ├─ data_planejada, ativo
│  └─ foto
└─ Properties:
   ├─ valor_disponivel_planejado: retorna valor_ja_reservado
   └─ falta_interna: valor_previsto - valor_ja_reservado
```

---

## 2. FLUXO DE DADOS CRÍTICO

### 2.1 Fluxo: Venda → Financeiro

```
1. Usuário cria Venda em VendaCreateView
   ├─ form_valid() → super().form_valid() → self.object = venda
   ├─ Chama _sync_venda_financeiro(venda)
   │  ├─ Se status_pagamento == PAGO:
   │  │  ├─ Cria/atualiza LancamentoFinanceiro
   │  │  └─ tipo=ENTRADA, categoria=VENDA
   │  └─ Se status_pagamento != PAGO:
   │     └─ Deleta LancamentoFinanceiro se existe
   └─ Mensagem de sucesso/aviso retorna ao usuário

2. Se atualiza Venda em VendaUpdateView
   ├─ Similar a criação
   ├─ Pode mudar de não-pago → pago (cria entrada)
   └─ Pode mudar de pago → não-pago (deleta entrada)

3. Se deleta Venda em VendaDeleteView
   ├─ Deleta LancamentoFinanceiro vinculado (se existe)
   └─ Deleta Venda

PROBLEMA: Sem @transaction.atomic - se LancamentoFinanceiro.delete() falhar, Venda é deletada mesmo assim!
```

### 2.2 Fluxo: Estoque e ConsumoPor Lote

```
1. MovimentoEstoque.save() é chamado
   ├─ Se criação (pk is None):
   │  ├─ Carrega ItemEstoque atual
   │  ├─ Se tipo=ENTRADA: quantidade_atual += quantidade, recalcula custo_medio
   │  ├─ Se tipo=SAIDA: quantidade_atual -= quantidade
   │  ├─ Se tipo=AJUSTE: quantidade_atual = quantidade
   │  └─ super().save()
   └─ item.save() → Salva ItemEstoque

2. Lote.custo_racao (property) é acessado
   ├─ Faz Query: MovimentoEstoque.objects.filter(lote_relacionado=self, item__categoria=RACAO)
   ├─ Calcula .aggregate(total=Sum("custo_unitario"))
   └─ Retorna total or 0

3. Lote.lucro_final (property) é acessado
   ├─ Chama custo_racao (query 1)
   ├─ Chama despesas_extras (query 2)
   ├─ Chama receita_vendas (query 3)
   └─ Retorna receita - (racao + extras)

PROBLEMA: N+1 explosivo em listas de lotes!
```

### 2.3 Fluxo: Incubação → Nascimento → Lote

```
1. Incubacao.save() chamado
   ├─ Se sem previsao_eclosao: auto-calcula data_entrada + 21 dias
   └─ Salva

2. Nascimento.save() chamado
   ├─ Valida quantidades (viva + morta = nascida)
   ├─ Recalcula automatic quantidade_nascida
   ├─ Vincula a Lote (lote_destino) [PROTECT]
   └─ Salva

3. Lote.resumo_incubacao (property) é acessado
   ├─ Query: incubacoes = self.incubacoes.all()
   ├─ Query: nascimentos = self.nascimentos.all()
   ├─ Calcula taxas
   └─ Retorna dict com resumo

PROBLEMA: No LoteDetailView, não usa prefetch_related, faz queries extras!
```

---

## 3. ANÁLISE DE PROBLEMAS ESTRUTURAIS (TOP 5)

### 🔴 PROBLEMA 1: QUERIES N+1 NAS PROPERTIES DO LOTE (CRÍTICO)

**Localização:** [lotes/models.py](lotes/models.py) - Properties nas linhas 45-98

**Descrição:**
Lote tem 9 properties que fazem queries diretas (não otimizadas):
- `custo_racao` (linha 59): Query MovimentoEstoque
- `despesas_extras` (linha 66): Query LancamentoFinanceiro
- `receita_vendas` (linha 74): Query Venda
- `custo_sanitario` (linha 81): Query LancamentoFinanceiro (segunda!)
- `consumo_racao_total` (linha 92): Query MovimentoEstoque (segunda!)
- `resumo_incubacao` (linha 107): Queries Incubacao + Nascimento (lista completa)

**Cascata crítica:**
```python
# Em LoteDetailView.get_context_data()
lote.resumo = {
    "mortalidade": lote.mortalidade_percentual,  # OK = Cálculo
    "consumo_racao": consumo_racao,              # OK = Já calculado
    "conversao": lote.conversao_alimentar,       # RUIM! Chama consumo_racao_total (query)
}
```

**Impacto:**
- **LoteListView** com 20 lotes/página → **7+ queries por lote** = ~140+ queries!
- **LoteDetailView**: prefetch_related(`movimentoestoque_set`) mas depois filtra em Python
- Sem select_related das relações de financeiro/vendas/estoque

**Exemplo do Problema:**
```python
# Em LoteListView (linha 33 de lotes/views.py)
ctx["comparativo"] = Lote.objects.aggregate(
    media_quantidade=Avg("quantidade_atual"),
    media_custo=Avg("custo_acumulado"),  # OK
)
# Mas depois em cada linha da tabela, se acessar lote.lucro_final:
# lucro_final → receita_vendas (query)
#             → despesas_extras (query)
#             → custo_racao (query)
```

**Solução Necessária:**
- Refatorar properties para usar values já calculados
- Usar annotations em QuerySet em vez de properties
- Criar serviço `LoteAnalyticsService` com cálculos otimizados
- Adicionar prefetch_related em get_queryset()

---

### 🔴 PROBLEMA 2: SINCRONIZAÇÃO VENDA-FINANCEIRO NÃO ATÔMICA (CRÍTICO)

**Localização:** [vendas/views.py](vendas/views.py) - Função `_sync_venda_financeiro()` (linhas 15-66)

**Descrição:**
A sincronização entre Venda e LancamentoFinanceiro não usa `@transaction.atomic`. Cenários de falha:

```python
# Cenário 1: Deletar Venda
def delete(self, request, *args, **kwargs):  # linha 196
    lancamento = getattr(self.object, "lancamento_financeiro", None)
    if lancamento:
        lancamento.delete()  # ← Se falhar aqui
    super().delete(request, *args, **kwargs)  # → Venda deletada mesmo assim!
```

```python
# Cenário 2: Atualizar Venda
if lancamento:
    for field, value in defaults.items():
        setattr(lancamento, field, value)  # Múltiplas atribuições
    lancamento.save()  # ← Pode falhar depois de mudanças
    logger.info(...)  # ← Log após falha = inconsistência
```

**Problema OneToOneField:**
- `LancamentoFinanceiro.venda` é OneToOneField
- Se alguém deletar lançamento diretamente no admin, Venda fica órfã
- Se alguém criar 2º lançamento com mesma venda, violação de constraint (não tratada)

**Impacto:**
- **Inconsistência de dados:** Venda paga sem entrada financeira
- **Vazamento de valores:** Entrada deletada, vendas não amortizadas
- **Auditoria comprometida:** Histórico não rastreia falhas

**Verificação:**
```python
# Teste rápido: quantas vendas pagas sem entrada?
SELECT COUNT(*) FROM vendas_venda v 
WHERE v.status_pagamento = 'pago' 
AND NOT EXISTS (SELECT 1 FROM financeiro_lancamentofinanceiro f WHERE f.venda_id = v.id);
```

**Solução Necessária:**
- Envolver `_sync_venda_financeiro()` em `@transaction.atomic`
- Adicionar signal `post_delete` para validar orfandade
- Criar modelo intermediário ou banco de dados constraint

---

### 🔴 PROBLEMA 3: DUPLICAÇÃO DE LÓGICA EM SANIDADE (ALTO)

**Localização:** [sanidade/models.py](sanidade/models.py)

**Código Duplicado:**
`AplicacaoVacina` (linhas 58-143) vs `VacinaLote` (linhas 173-250)

**Properties idênticas:**
| Property | AplicacaoVacina | VacinaLote | Linhas |
|----------|-----------------|-----------|--------|
| `atrasada` | linha 91 | linha 207 | **SÃO IGUAIS** |
| `prevista_hoje` | linha 94 | linha 211 | **SÃO IGUAIS** |
| `proxima` | linha 98 | linha 215 | **SÃO IGUAIS** |
| `status_operacional` | linha 102 | linha 219 | **SÃO IGUAIS** |
| `status_operacional_label` | linha 108 | linha 225 | **SÃO IGUAIS** |
| `urgencia_operacional` | linha 120 | linha 237 | **SÃO IGUAIS** |

**Código da duplicação:**
```python
# AplicacaoVacina.status_operacional (linha 102)
@property
def status_operacional(self):
    if self.status == self.STATUS_APLICADA:
        return "aplicada"
    if self.status == self.STATUS_CANCELADA:
        return "cancelada"
    if self.atrasada:
        return "atrasada"
    # ... 7 mais linhas iguais

# VacinaLote.status_operacional (linha 219)
@property
def status_operacional(self):
    if self.aplicada:  # ← Diferente apenas este (mas lógica similar)
        return "aplicada"
    if self.atrasada:
        return "atrasada"
    # ... resto é igual!
```

**Problema:**
- Se bugou em `atrasada`, precisa corrigir em 2 lugares
- Manutenção cara (taxa de divergência alta)
- Testes precisam cobrir ambas redundantemente

**Impacto:**
- **Bugs silenciosos:** Correção em um lugar, outro fica errado
- **Maintenção:** +50% de esforço
- **Testes:** Duplicação de casos de teste

**Solução Necessária:**
- Criar mixin `VacinacaoOperacionalMixin` com properties compartilhadas
- Ou usar model inheritance
- Centralizar lógica em serviço `VacinacaoService`

---

### 🔴 PROBLEMA 4: FALTA DE TRANSAÇÕES ATÔMICAS EM MOVIMENTOESTOQUE (CRÍTICO)

**Localização:** [estoque/models.py](estoque/models.py) - `MovimentoEstoque.save()` (linhas 73-87)

**Descrição:**
```python
def save(self, *args, **kwargs):
    creating = self.pk is None
    item = self.item
    if creating and item:
        qtd_atual = item.quantidade_atual or 0
        # Múltiplas operações SEM transação
        if self.tipo == self.TIPO_ENTRADA:
            novo_qtd = qtd_atual + (self.quantidade or 0)  # ← Cálculo
            if self.custo_unitario:
                item.ultimo_preco = self.custo_unitario
                total_custo = (item.custo_medio or 0) * qtd_atual + ...  # ← Mais cálculos
                if novo_qtd:
                    item.custo_medio = total_custo / novo_qtd
        # ...
        item.quantidade_atual = novo_qtd  # ← Atribuição
    super().save(*args, **kwargs)  # ← PODE FALHAR AQUI
    if creating and item:
        item.save()  # ← Se falhar na linha anterior, item fica inconsistente!
```

**Cenário de Falha:**
1. Cria MovimentoEstoque (entrada de 100 kg de ração)
2. Calcula: ItemEstoque.quantidade_atual = 50 + 100 = 150
3. `super().save()` falha (erro de banco de dados, timeout, etc)
4. `item.save()` nunca é chamado
5. MovimentoEstoque foi criado, mas ItemEstoque.quantidade_atual permanece 50!

**Solução Necessária:**
- Envolver em `@transaction.atomic` ou usar `transaction.atomic()` context manager
- Ou fazer `item.save()` antes de `super().save()`

---

### 🔴 PROBLEMA 5: VALIDAÇÕES E TRANSIÇÕES DE ESTADO FALTANDO (ALTO)

**Localização:** Vários models

**Exemplo 1: Ave.status (aves/models.py linha 22)**
```python
STATUS_VIVA = "viva"
STATUS_VENDIDA = "vendida"
STATUS_MORTA = "morta"
STATUS_ABATIDA = "abatida"
```

**Problema:**
- Sem validação de transições válidas!
- Ave pode ir de ABATIDA → VIVA (absurdo!)
- Ave pode ir de VENDIDA → MORTA (absurdo!)
- Nenhuma regra de negócio no save()

**Exemplo 2: Lote.quantidade_atual pode ficar negativa**
```python
# Em Lote (lotes/models.py), sem validação de:
# - quantidade_atual nunca pode < 0
# - quantidade_atual nunca pode > quantidade_inicial (em teoria)
```

Se MovimentoEstoque.SAIDA for maior que quantidade, fica negativa.

**Exemplo 3: Incubacao.ovos_fertis + ovos_infertis pode > quantidade_ovos**
```python
# Sem validação em Incubacao.save()
# Poderia ter 100 ovos, mas 80 fertis + 50 infértis = 130 (maior!)
```

**Impacto:**
- **Dados sujos:** Relatórios errados
- **Negócio:** Decisões baseadas em dados inválidos
- **Auditoria:** Impossível confiar no histórico

**Solução Necessária:**
- Adicionar clean() e validações em save()
- Usar Django validators
- Criar máquina de estados (FSM) para Ave

---

## 4. GAPS DE INTEGRAÇÃO ENTRE MÓDULOS

### Gap 1: Venda → Financeiro (IMPLEMENTADO MAS FRÁGIL)

**Status:** Semi-integrado com riscos

**Problema:**
- Depende de chamar `_sync_venda_financeiro()` na view
- Sem garantia transacional
- Se usuário criar LancamentoFinanceiro manualmente sem vinc venda, ambos podem coexistir

**Verificação:**
```python
# Lançamentos sem venda vinculada
LancamentoFinanceiro.objects.filter(venda__isnull=True, tipo='entrada', categoria='venda').count()
# Se > 0, há desincronização!
```

---

### Gap 2: MovimentoEstoque → Lote (LOOSELY COUPLED)

**Status:** Remoto - ForeignKey SET_NULL

**Problema:**
- MovimentoEstoque.lote_relacionado é optional
- Não há validação que lote exista se movimento é consumo
- Relatório de consumo por lote pode ficar incompleto

**Pergunta sem resposta:**
- Se movimento é consumo, por qual lote foi?
- Se SET_NULL ocorre, perdem-se dados históricos

---

### Gap 3: Venda.ave vs Venda.lote (AMBIGUIDADE)

**Status:** Ambíguo

**Problema:**
- Venda pode ter ambos, nenhum, ou um invertido
- Sem validação
- LancamentoFinanceiro.ave e LancamentoFinanceiro.lote também ambos

**Questão:**
- Se venda de Ave individual, deve ter ave e lote?
- Se venda de lote inteiro, deve ter apenas lote?
- Sem contrato explícito!

---

### Gap 4: Incubacao → Nascimento → Lote (BRITTLE)

**Status:** Conectado mas sem validações

**Problema:**
- Nascimento.lote_destino é PROTECT
- Se tentar deletar Lote com nascimentos, erro
- Mas Incubacao pode ter quantidade_nascida diferente de sum(nascimentos.quantidade_nascida)
- Sem sincronização bidirecional

---

### Gap 5: Reprodutor → Ave → Lote (WEAK)

**Status:** OneToOne frágil

**Problema:**
- Reprodutor OneToOne Ave
- Como saber em qual Lote o reprodutor está agora?
- Ave.lote_atual pode ser NULL
- Histórico de reprodutor por lote não existe!

---

## 5. DUPLICAÇÃO DE CÓDIGO (CÓDIGO DUPLICADO)

### Duplicação 1: Properties de Vacinação

**Arquivo:** [sanidade/models.py](sanidade/models.py)

| Código | AplicacaoVacina | VacinaLote |
|--------|-----------------|-----------|
| `data_final_carencia` | Linha 87 | Linha N/A (VacinaLote não tem) |
| `carencia_ativa` | Linha 90 | Linha N/A |
| `atrasada` | Linha 91 | Linha 207 |
| `prevista_hoje` | Linha 94 | Linha 211 |
| `proxima` | Linha 98 | Linha 215 |
| `status_operacional` | Linha 102 | Linha 219 |

**Status:** ~65 linhas de código duplicado em sanidade/models.py

---

### Duplicação 2: Lógica de Carência (Vacina vs Medicamento)

**Arquivo:** [sanidade/models.py](sanidade/models.py)

```python
# AplicacaoVacina.carencia_ativa (linha 90)
@property
def carencia_ativa(self):
    fim = self.data_final_carencia
    return bool(fim and fim >= timezone.localdate())

# Tratamento.carencia_ativa (linha 341)
@property
def carencia_ativa(self):
    fim = self.data_final_carencia
    return bool(fim and fim >= timezone.localdate())
```

**Duplicação:** 3 linhas idênticas em 2 classes

---

### Duplicação 3: Cálculos de Tax Eclosão

**Arquivo:** [lotes/models.py](lotes/models.py) e [incubacao/models.py](incubacao/models.py)

```python
# Lote.resumo_incubacao (lotes/models.py linha 118)
taxa_eclosao = 0
if total_ovos:
    taxa_eclosao = (total_nascidos / total_ovos) * 100

# Incubacao.taxa_eclosao (incubacao/models.py linha 49)
@property
def taxa_eclosao(self):
    if self.ovos_fertis:
        return (self.quantidade_nascida / self.ovos_fertis) * 100
    return 0
```

**Problema:** Fórmulas ligeiramente diferentes (ovos_fertis vs total_ovos)

---

### Duplicação 4: Acesso a `timezone.localdate()`

**Arquivo:** Múltiplos arquivos

**Contagem:** 50+ aparições de `timezone.localdate()` em:
- sanidade/models.py: 15+ vezes
- lotes/views.py: 8+ vezes
- estoque/views.py: 5+ vezes
- historico/signals.py: 0 (não usa)

**Melhor Prática:** Criar função centralizada `get_hoje()` em `core/utils.py`

---

## 6. ÍNDICES DE BANCO DE DADOS (OTIMIZAÇÃO)

### Índices Existentes:

**Bons:**
- `estoque_ite_categor_3c8216_idx`: ItemEstoque(categoria, nome) ✓
- `estoque_mov_item_id_f51f97_idx`: MovimentoEstoque(item_id, data) ✓
- `financeiro__venda_i_340fc8_idx`: LancamentoFinanceiro(venda) ✓
- `historico_h_entidad_1995bc_idx`: HistoricoEvento(entidade, referencia_id, created_at) ✓

### Índices FALTANDO:

| Tabela | Campo(s) | Por quê |
|--------|----------|--------|
| `aves_ave` | (`finalidade`, `status`) | Filtros comuns em listagens |
| `aves_ave` | (`lote_id`, `status`) | Buscar aves no lote com status |
| `lotes_lote` | (`status`, `finalidade`) | Filtros principais |
| `vendas_venda` | (`cliente`, `data`) | Busca por cliente |
| `nascimentos` | (`lote_id`, `data`) | Histórico por lote |
| `abate_abate` | (`lote_id`, `data`) | Histórico por lote |
| `sanidade_aplicacaovacina` | (`lote_id`, `data_programada`) | Vacinação schedule |

---

## 7. RECOMENDAÇÕES PARA FASE 1 (Prioritário)

### 🎯 FASE 1: Fundação Sólida (2-3 semanas)

#### 1.1 Corrigir Sincronização Venda-Financeiro (CRITÉRIO BLOQUEADOR)

**Arquivo:** [vendas/views.py](vendas/views.py)

**Tarefas:**
```python
# 1. Envolver em transação
from django.db import transaction

@transaction.atomic
def _sync_venda_financeiro(venda):
    # ... código existente
    
# 2. Adicionar validação
def clean_venda_sync(venda):
    # Validar estado transicional
    # Evitar duplicação
    
# 3. Adicionar signal
@receiver(post_save, sender=Venda)
def sync_venda_financeiro_signal(sender, instance, created, **kwargs):
    # Sincronizar automaticamente sem precisar chamar na view
```

**Teste:**
```python
def test_venda_sync_atomico():
    venda = Venda.objects.create(..., status_pagamento='pago')
    assert venda.tem_entrada_financeira
    
    venda.status_pagamento = 'pendente'
    venda.save()
    assert not venda.tem_entrada_financeira
```

---

#### 1.2 Otimizar Queries de Lote (N+1)

**Arquivo:** [lotes/models.py](lotes/models.py) e [lotes/views.py](lotes/views.py)

**Tarefas:**
```python
# 1. Criar serviço de análise
# core/services/lote_analytics.py
class LoteAnalyticsService:
    @staticmethod
    def get_resumo_completo(lote):
        # Fazer 1 query com .prefetch_related ao invés de N
        return {...}
        
# 2. Refatorar LoteListView
class LoteListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'linhagem_principal'
        ).prefetch_related(
            'aves', 
            'vendas', 
            'movimentoestoque_set__item',
            'lancamentos'  # ← Novo
        )
    
# 3. Refatorar properties complexas
# Em vez de property dinâmica, usar @cached_property em Python 3.8+
from functools import cached_property

@cached_property
def custo_racao(self):
    # Agora só faz query 1 vez por instância
    return (...)
```

**Teste:**
```python
def test_lote_list_queries(self):
    Lote.objects.bulk_create([...10 lotes...])
    with self.assertNumQueries(5):  # Esperado: 1 (lista) + 4 (prefetch)
        list(LoteListView().get_queryset())
```

---

#### 1.3 Adicionar Validações de Estado

**Arquivo:** [aves/models.py](aves/models.py)

**Tarefas:**
```python
# 1. Adicionar máquina de estados
from enum import Enum

class AveStatus(Enum):
    VIVA = ('viva', {'transicoes_para': ['vendida', 'morta', 'abatida']})
    VENDIDA = ('vendida', {'transicoes_para': []})
    MORTA = ('morta', {'transicoes_para': []})
    ABATIDA = ('abatida', {'transicoes_para': []})

# 2. Adicionar clean() method
def clean(self):
    if self.status == 'vendida' and not self.valor_referencia:
        raise ValidationError("Ave vendida precisa de valor de referência")
        
# 3. Adicionar em save()
def save(self, *args, **kwargs):
    self.full_clean()
    super().save(*args, **kwargs)
```

**Também em:**
- [lotes/models.py](lotes/models.py): validar quantidade_atual >= 0
- [incubacao/models.py](incubacao/models.py): validar ovos_fertis + ovos_infertis <= quantidade_ovos
- [movimentoestoque/models.py](estoque/models.py) - será necessário refatorar

---

#### 1.4 Eliminar Duplicação de Sanidade

**Arquivo:** [sanidade/models.py](sanidade/models.py)

**Tarefas:**
```python
# 1. Criar mixin
class VacinacaoOperacionalMixin:
    """Mixin com properties compartilhadas entre AplicacaoVacina e VacinaLote"""
    
    @property
    def atrasada(self):
        hoje = timezone.localdate()
        programada = self.get_data_programada()  # ← Abstrato, implementar em subclass
        return bool(self.get_status_pendente() and programada < hoje)
    
    @property
    def status_operacional(self):
        # ... implementação única compartilhada

# 2. Aplicar em ambas as classes
class AplicacaoVacina(VacinacaoOperacionalMixin, ...):
    def get_data_programada(self):
        return self.data_programada
    def get_status_pendente(self):
        return self.status == self.STATUS_PENDENTE

class VacinaLote(VacinacaoOperacionalMixin, ...):
    def get_data_programada(self):
        return self.data_prevista
    def get_status_pendente(self):
        return not self.aplicada
```

---

#### 1.5 Adicionar Transações Atômicas

**Arquivo:** [estoque/models.py](estoque/models.py)

**Tarefas:**
```python
from django.db import transaction

def save(self, *args, **kwargs):
    creating = self.pk is None
    with transaction.atomic():  # ← Envolver tudo
        super().save(*args, **kwargs)
        if creating and self.item:
            item = self.item
            # ... atualiza item
            item.save()
```

---

#### 1.6 Criar Índices de Base de Dados

**Arquivo:** [novas migrations](migrations/)

**Tarefas:**
```python
# migrations/0001_add_indexes.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('aves', '0001_initial'),
        ('lotes', '0001_initial'),
        # ... etc
    ]

    operations = [
        migrations.AddIndex(
            model_name='ave',
            index=models.Index(fields=['finalidade', 'status'], name='aves_finalidade_status_idx'),
        ),
        migrations.AddIndex(
            model_name='lote',
            index=models.Index(fields=['status', 'finalidade'], name='lotes_status_finalidade_idx'),
        ),
        # ... mais índices
    ]
```

---

#### 1.7 Refatorar Reprodutor-Ave

**Arquivo:** [reprodutores/models.py](reprodutores/models.py) + [lotes/models.py](lotes/models.py)

**Problema:** Reprodutor(Ave) sem saber em qual Lote está

**Tarefas:**
```python
# 1. Adicionar ForeignKey histórico
class HistoricoReprodutorLote(TimeStampedModel):
    reprodutor = ForeignKey(Reprodutor, on_delete=CASCADE)
    lote = ForeignKey(Lote, on_delete=SET_NULL, null=True)
    data_inicio = DateField()
    data_fim = DateField(null=True, blank=True)
    
# 2. Adicionar signal em Lote para trackear reprodutores
@receiver(post_save, sender=Lote)
def track_reprodutores_em_lote(sender, instance, **kwargs):
    # Se Lote é reprodutivo, rastrear quais reprodutores estão aqui
```

---

### 📊 Tabela de Priorização FASE 1

| ID | Tarefa | Criticidade | Esforço | Dependência |
|----|--------|-------------|--------|------------|
| 1.1 | Sincronização Venda-Financeiro | 🔴 Crítica | 4h | - |
| 1.2 | Otimizar N+1 de Lote | 🔴 Crítica | 6h | - |
| 1.3 | Validações de Estado | 🟠 Alta | 5h | - |
| 1.4 | Eliminar Duplicação Sanidade | 🟠 Alta | 4h | - |
| 1.5 | Transações Atômicas | 🟠 Alta | 3h | 1.1 |
| 1.6 | Índices de BD | 🟡 Média | 2h | - |
| 1.7 | Reprodutor Tracking | 🟡 Média | 4h | - |

**Total Estimado FASE 1:** ~28 horas (1 developer × 4 dias)

---

## 8. RESUMO EXECUTIVO

### Força do Sistema

✅ **Estrutura de Base Sólida:** TimeStampedModel, AuditModel, AtivoInativoModel reutilizáveis  
✅ **Cobertura de Domínio:** Todos os módulos principais (aves, lotes, financeiro, estoque, sanidade) presentes  
✅ **Signals para Histórico:** HistoricoEvento bem estruturado  
✅ **Relacionamentos Bem Definidos:** Maioria das ForeignKeys com on_delete apropriado  

### Fraquezas Críticas

❌ **N+1 Explosivo:** Properties de Lote fazem queries sem otimização  
❌ **Sem Transações Atômicas:** Risco de inconsistência Venda/Financeiro  
❌ **Duplicação de Lógica:** 65+ linhas duplicadas em Sanidade  
❌ **Validações Faltando:** Transições de estado sem contrato (Ave.status)  
❌ **Gaps de Integração:** Venda/Financeiro manual, Reprodutor sem localização  

### Recomendação

**IMPLEMENTAR FASE 1 ANTES DE QUALQUER EXPANSÃO**

O sistema necessita de **refatoração estrutural** (não apenas novos features) para suportar crescimento. Investir 28 horas agora evita débito técnico exponencial.

---

**Análise concluída:** 12 de abril de 2026  
**Avaliação Geral:** ⭐⭐⭐ (3/5 - Estrutura OK, Qualidade Média, Risco Alto)

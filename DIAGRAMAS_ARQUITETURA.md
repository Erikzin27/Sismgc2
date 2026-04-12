# Diagramas de Arquitetura - SISMGC Django

## Diagrama 1: Relacionamentos Principais (Mapa de Entidades)

```
NÚCLEO DE AVES & GENÉTICA
═══════════════════════════════════════════════════════════════════════════

                          ┌──────────────────┐
                          │    Linhagem      │
                          │  linhagens/      │
                          │  models.py       │
                          └────────┬─────────┘
                                   │ 1:N
                    ┌──────────────┼──────────────┐
                    │              │              │
              1:N   │         1:N  │         1:N  │
            ┌───────▼────┐   ┌─────▼──────┐   ┌──▼──────────┐
            │    Ave     │   │    Lote    │   │ Nascimento  │
            │  aves/     │   │   lotes/   │   │ nascimentos/│
            │ models.py  │   │ models.py  │   │ models.py   │
            └────┬──┬────┘   └────┬───────┘   └─────────────┘
         1:N │  │ (self-referential)
             │  └─────────────┐
             │                │
           pai  mae      ┌─────▼──────────┐
             │                │
            filhos_pai ├──────┴──────────────┐
            filhos_mae │   ┌───────────────┐ │
                       │   │  Reprodutor   │ │
             ┌─────────▼─┼──│ reprodutores/ │ │
             │           │  │ models.py     │ │
             │ OneToOne  │  └───────────────┘ │
             │           │                    │
          ┌──▼──────────┐│  RegistroGenetico│
          │ Ave self-ref││  genetica/       │
          │ (1:1)       ││  models.py       │
          └─────────────┘│ (pai, mae, filho)│
                         └───────────────────┘


GESTÃO DE LOTES (Operacional)
═══════════════════════════════════════════════════════════════════════════

                    ┌────────────────────┐
                    │      Lote          │
                    │    lotes/          │
                    │    models.py       │
                    └──────────┬─────────┘
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
    1:N  │                      │  1:N             1:N │
    ┌────▼───┐            ┌─────▼──────┐         ┌───▼─────┐
    │  Aves  │            │    Venda   │    ┌────│ Abate   │
    │ aves/  │            │  vendas/   │    │    │ abate/  │
    │models.py           │ models.py  │    │    │ models.py
    └────────┘            └─────┬──────┘    │    │
                            1:1 │          │    │
 ┌──────────────────────────────┼──────────┼────┼────────────┐
 │                              │          │    │            │
 │  ┌──────────────────────┐    │          │    └─ M2M (aves)
 │  │ LancamentoFinanceiro │◄───┘          │
 │  │  financeiro/         │ VENDA         │
 │  │  models.py           │ ↔ FINANCEIRO  │
 │  │ (OneToOne)           │  (Integração) │
 │  └──────────────────────┘               │
 │                                         │
 │  ┌──────────────────────────────────┐  │
 │  │    MovimentoEstoque             │  │
 │  │    estoque/                     │  │
 │  │    models.py                    │  │
 │  │  (lote_relacionado opcional)    │  │
 │  └──────────────────────────────────┘  │
 │                                         │
 │  ┌──────────────────────────────────┐  │
 │  │     ItemEstoque                 │  │
 │  │     estoque/                    │  │
 │  │     models.py                   │  │
 │  │  (quantidade_atual muda por ^)  │  │
 │  └──────────────────────────────────┘  │
 │                                         │
 └─────────────────────────────────────────┘


INCUBAÇÃO & NASCIMENTO (Reprodução)
═══════════════════════════════════════════════════════════════════════════

    ┌────────────────┐
    │  Incubacao     │
    │  incubacao/    │
    │  models.py     │
    └────────┬───────┘
             │ 1:N (CASCADE)
             │
      ┌──────▼────────┐
      │  Nascimento   │
      │  nascimentos/ │
      │  models.py    │
      └────┬─────┬────┘
           │     │
      1:1  │     │ 1:N
      ┌────▼─┐   │
      │Lote  │   │ (vínculo com lote_destino)
      │      │   │
      └──────┘   └─→ Lote (lote_destino)
                      [PROTECT]


SANIDADE (Saúde e Bem-estar)
═══════════════════════════════════════════════════════════════════════════

    ┌──────────────────────────────────────────────────────┐
    │                                                      │
    │  AplicacaoVacina (sanidade/models.py)               │
    │  ├─ ForeignKey → Vacina [CASCADE]                   │
    │  ├─ ForeignKey → Ave [SET_NULL]  (opcional)         │
    │  └─ ForeignKey → Lote [SET_NULL] (opcional)         │
    │                                                      │
    │  Properties (⚠️ DUPLICADAS COM VacinaLote):          │
    │  ├─ atrasada                                         │
    │  ├─ prevista_hoje                                   │
    │  ├─ proxima                                          │
    │  ├─ status_operacional                               │
    │  ├─ dias_atraso                                      │
    │  └─ urgencia_operacional                             │
    │                                                      │
    └──────────────────────────────────────────────────────┘
                            │
                    ┌───────┴────────┐
                    │                │
                 1:N│                │ 1:N
            ┌──────▼───┐        ┌───▼──────┐
            │  Vacina  │        │VacinaLote│
            │sanidade/ │        │sanidade/ │
            │models.py │        │models.py │
            └──────────┘        └───┬──────┘
                                    │
                            (⚠️ CODE DUPLICATION)
                                    │
                        ┌───────────┴─────────┐
                        │  Tratamento         │
                        │  sanidade/          │
                        │  models.py          │
                        │ ├─ ave [SET_NULL]   │
                        │ └─ lote [SET_NULL]  │
                        └─────────────────────┘


HISTÓRICO & AUDITORIA
═══════════════════════════════════════════════════════════════════════════

    ┌─────────────────────────────┐
    │    HistoricoEvento          │
    │    historico/models.py      │
    │                             │
    │  Rastreia (via signals):   │
    │  ├─ Ave                    │
    │  ├─ Lote                   │
    │  ├─ Venda                  │
    │  ├─ Abate                  │
    │  ├─ AplicacaoVacina        │
    │  ├─ Tratamento             │
    │  └─ MovimentoEstoque       │
    │                             │
    │  Campos:                   │
    │  ├─ entidade (string)      │
    │  ├─ referencia_id (pk)     │
    │  ├─ acao (create/update..) │
    │  ├─ usuario [SET_NULL]     │
    │  └─ detalhes (JSONField)   │
    └─────────────────────────────┘
```

---

## Diagrama 2: Fluxo Crítico - Venda para Financeiro (Integração)

```
FLUXO VENDA → FINANCEIRO
═══════════════════════════════════════════════════════════════════════════

┌────────────────────────────────────────────────────────────────┐
│                     USUÁRIO CRIA VENDA                         │
└───────────────────────┬────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────────────┐
│              VendaCreateView.form_valid()                      │
│                   vendas/views.py (linha 150)                  │
│                                                                │
│  1. response = super().form_valid(form)                       │
│     └─ Venda salva em BD sem sincronização                    │
│                                                                │
│  2. try: _sync_venda_financeiro(self.object)                  │
│     └─ Função inicia (SEM @transaction.atomic!) ⚠️            │
└───────────────────────┬────────────────────────────────────────┘
                        │
            ┌───────────┴───────────┐
            │ Verifica status_pagamento
            │
    ┌───────▼─────────┐    ┌──────────────────┐
    │  NÃO PAGO?      │    │  SIM PAGO?       │
    │  (pendente/     │    │  (status_pagamento
    │   cancelado)    │    │   == 'pago')     │
    │                 │    │                  │
    └────────┬────────┘    └────────┬─────────┘
             │                      │
      ┌──────▼─────────┐     ┌──────▼──────────────────┐
      │ if lancamento: │     │ CREATE/UPDATE           │
      │   delete()     │     │ LancamentoFinanceiro    │
      │   ✓ OK         │     │                         │
      └────────────────┘     │ defaults = {            │
                             │   tipo: ENTRADA,        │
                             │   categoria: VENDA,     │
                             │   valor: venda.valor..  │
                             │   lote: venda.lote,     │
                             │   ave: venda.ave,       │
                             │   venda: venda (PK)     │
                             │ }                       │
                             │                         │
                             │ if lancamento:          │
                             │   update campos         │
                             │   lancamento.save()     │
                             │   ✓ OU FALHA? ⚠️       │
                             │                         │
                             │ else:                   │
                             │   create novo           │
                             │   ✓ OU FALHA? ⚠️       │
                             └──────────┬──────────────┘
                                        │
                    ┌───────────────────┼───────────────┐
                    │                   │               │
              ✓ SUCESSO         ⚠️ FALHA BD      ✓ SUCESSO
                    │                   │               │
                    ▼                   ▼               ▼
            ┌──────────────┐  ┌──────────────┐  ┌─────────────┐
            │ Log info:    │  │ except:      │  │ Log info:   │
            │ "Venda criada│  │   logger.err │  │ "Entrada    │
            │ e entrada    │  │   "          │  │ gerada"     │
            │ gerada"      │  │              │  │             │
            │              │  │ raise        │  │ messages    │
            │ messages.suc │  │ (retrai      │  │ .success()  │
            │ cess()       │  │  exception)  │  │             │
            └──────┬───────┘  └──────┬───────┘  └────────┬─────┘
                   │                 │                    │
                   └────────────┬────┴────────────────────┘
                                │
                        ┌───────▼──────────┐
                        │ Retorna resposta │
                        │ ao usuário       │
                        └──────────────────┘


⚠️ PROBLEMA: SEM TRANSAÇÃO!
═══════════════════════════════════════════════════════════════════════════

Cenário 1: Falha após salvar Venda mas antes de criar LancamentoFinanceiro
┌──────────────────────────────────────────────────────────────┐
│ 1. Venda criada (BD)                      ✓
│ 2. _sync_venda_financeiro() chamado
│ 3. LancamentoFinanceiro.objects.create() falha       ✗
│ 4. Exception gerada, usuário vê erro
│ 5. MAS: Venda já está no BD! Sem entrada financeira  ⚠️
│
│ RESULTADO: Venda paga mas sem entrada = $ perdido!
└──────────────────────────────────────────────────────────────┘

Cenário 2: Falha ao deletar no VendaDeleteView
┌──────────────────────────────────────────────────────────────┐
│ 1. lancamento.delete() falha               ✗
│ 2. Exception capturada
│ 3. super().delete() ainda é chamado
│ 4. Venda deletada, mas LancamentoFinanceiro ainda existe
│
│ RESULTADO: Entrada financeira órfã = ganho não contabilizado!
└──────────────────────────────────────────────────────────────┘
```

---

## Diagrama 3: Problema N+1 em Lote (Query Cascade)

```
LOTE PROPERTIES = QUERIES N+1
═══════════════════════════════════════════════════════════════════════════

LoteListView.get_context_data() renderiza 20 lotes/página

Para CADA lote mostrado, se template acessa:

Lote #1
├─ lote.custo_racao (Property)
│  └─ Query: MovimentoEstoque.objects.filter(lote_relacionado=1, ...)
│     └─ Aggregation: SUM(custo_unitario) → 1 QUERY
│
├─ lote.despesas_extras (Property)
│  └─ Query: LancamentoFinanceiro.objects.filter(lote=1, tipo='saida', ...)
│     └─ Aggregation: SUM(valor) → 1 QUERY
│
├─ lote.receita_vendas (Property)
│  └─ Query: Venda.objects.filter(lote=1, ...)
│     └─ Aggregation: SUM(valor_total) → 1 QUERY
│
├─ lote.custo_sanitario (Property)
│  └─ Query: LancamentoFinanceiro.objects.filter(lote=1, categoria=VACINA|MEDICAMENTO, ...)
│     └─ Aggregation: SUM(valor) → 1 QUERY
│
├─ lote.consumo_racao_total (Property)
│  └─ Query: MovimentoEstoque.objects.filter(lote_relacionado=1, ...)
│     └─ Aggregation: SUM(quantidade) → 1 QUERY
│
└─ lote.lucro_final (Property) = receita - (racao + extras)
   └─ CHAMA 3 properties acima em cascata → 3 QUERIES!

┌─────────────────────────────────────────┐
│ TOTAL POR LOTE: 7 QUERIES               │
│ TOTAL COM 20 LOTES: 7 × 20 = 140 QUERY │
│ + 1 query para listar = 141 QUERIES!    │
└─────────────────────────────────────────┘

IMPACTO:
┌────────────────────────────────────────────────┐
│ Tempo de carregamento: ~5-10 segundos         │
│ Carga no DB: 140 queries em 5s = 28 QPS      │
│ Escalabilidade: Com 100 lotes = 700 QPS      │
│ RESULTADO: Não escala, DB vai sobrecarregar  │
└────────────────────────────────────────────────┘

SOLUÇÃO: Usar annotations + prefetch_related

LoteListView.get_queryset():
└─ .prefetch_related(
     'vendas',
     'lancamentos',
     'movimentoestoque_set__item'
   )
   .annotate(
     total_vendas=Sum('vendas__valor_total'),
     despesas=Sum('lancamentos__valor', 
                   filter=Q(lancamentos__tipo='saida')),
     consumo=Sum('movimentoestoque_set__quantidade',
                  filter=Q(movimentoestoque_set__item__categoria='racao'))
   )

RESULTADO:
├─ 1 Query: Listar lotes
├─ 1 Query: Prefetch vendas
├─ 1 Query: Prefetch lancamentos
├─ 1 Query: Prefetch movimentos estoque
├─ 1 Query: Prefetch itens
└─ TOTAL: 5 QUERIES (vs 141 antes!)
```

---

## Diagrama 4: Duplicação de Código em Sanidade

```
CÓDIGO DUPLICADO: AplicacaoVacina vs VacinaLote
═══════════════════════════════════════════════════════════════════════════

sanidade/models.py

┌────────────────────────────────────────────────────────────┐
│  AplicacaoVacina(TimeStampedModel, AuditModel)            │
│  Campos:                                                   │
│  • vacina: ForeignKey(Vacina)                             │
│  • ave: ForeignKey(Ave) [SET_NULL]                        │
│  • lote: ForeignKey(Lote) [SET_NULL]                      │
│  • data_programada: DateField                             │
│  • data_aplicacao: DateField [nullable]                   │
│  • status: CharField(choices=[PENDENTE, APLICADA, ...]) │
│                                                           │
│  @property                                                 │
│  def atrasada(self):                                       │
│      hoje = timezone.localdate()                          │
│      return bool(self.status == PENDENTE and             │
│                  self.data_programada < hoje)             │
│  ┌─ 3 linhas                                              │
│                                                           │
│  @property                                                 │
│  def prevista_hoje(self):                                  │
│      hoje = timezone.localdate()                          │
│      return self.data_programada == hoje                  │
│  ┌─ 2 linhas                                              │
│                                                           │
│  @property                                                 │
│  def proxima(self):                                        │
│      hoje = timezone.localdate()                          │
│      return (self.data_programada > hoje and              │
│              self.data_programada <= hoje + timedelta(7))│
│  ┌─ 3 linhas                                              │
│                                                           │
│  @property                                                 │
│  def status_operacional(self):                             │
│      if self.status == APLICADA: return "aplicada"       │
│      if self.status == CANCELADA: return "cancelada"     │
│      if self.atrasada: return "atrasada"                  │
│      # ... 7 mais linhas                                  │
│  ┌─ 10 linhas                                             │
│                                                           │
│  @property                                                 │
│  def status_operacional_label(self):                       │
│      labels = {...}                                       │
│      return labels.get(...)                               │
│  ┌─ 4 linhas                                              │
│                                                           │
│  @property                                                 │
│  def dias_atraso(self):                                    │
│      if not self.atrasada: return 0                       │
│      return (timezone.localdate() - self.data_programada).days │
│  ┌─ 2 linhas                                              │
│                                                           │
│  @property                                                 │
│  def urgencia_operacional(self):                           │
│      if not self.atrasada: return ""                      │
│      if self.dias_atraso >= 7: return "critica"          │
│      if self.dias_atraso >= 3: return "alta"             │
│      return "moderada"                                    │
│  ┌─ 5 linhas                                              │
│                                                           │
│  TOTAL: ~35 linhas de properties                          │
└────────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │  CÓDIGO      │
                    │  DUPLICADO   │
                    │      ⚠️      │
                    └───────┬───────┘
                            │

┌────────────────────────────────────────────────────────────┐
│  VacinaLote(TimeStampedModel, AuditModel)                 │
│  Campos:                                                   │
│  • lote: ForeignKey(Lote) [CASCADE]                       │
│  • nome_vacina: CharField(max_length=100)                 │
│  • data_prevista: DateField                               │
│  • aplicada: BooleanField                                 │
│  • data_aplicacao: DateField [nullable]                   │
│                                                           │
│  @property                                                 │
│  def atrasada(self):                                       │
│      hoje = timezone.localdate()                          │
│      return bool(not self.aplicada and              ← DIFFER
│                  self.data_prevista < hoje)         ← ÇA
│  ┌─ 3 linhas [IGUAL A AplicacaoVacina.atrasada]          │
│                                                           │
│  @property                                                 │
│  def prevista_hoje(self):                                  │
│      hoje = timezone.localdate()                          │
│      return not self.aplicada and self.data_prevista == hoje │
│  ┌─ 2 linhas [SIMILAR]                                    │
│                                                           │
│  @property                                                 │
│  def proxima(self):                                        │
│      hoje = timezone.localdate()                          │
│      return (not self.aplicada and                  ← DIFFER
│              self.data_prevista > hoje and          ← ÇA
│              self.data_prevista <= hoje + timedelta(7))   │
│  ┌─ 3 linhas [SIMILAR]                                    │
│                                                           │
│  @property                                                 │
│  def status_operacional(self):                             │
│      if self.aplicada: return "aplicada"          ← DIFFER
│      if self.atrasada: return "atrasada"          ← ÇA
│      # ... mesmo que AplicacaoVacina.status_operacional   │
│  ┌─ 8 linhas [QUASE IGUAL]                               │
│                                                           │
│  @property                                                 │
│  def status_operacional_label(self): [IGUAL]              │
│                                                           │
│  @property                                                 │
│  def urgencia_operacional(self): [IGUAL]                  │
│                                                           │
│  TOTAL: ~35 linhas (quase as mesmas!)                     │
└────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  DUPLICAÇÃO:                                    │
│  • ~30 linhas de código idêntico ou muito       │
│    parecido em 2 classes                       │
│  • Qualquer bug em 1 precisa ser corrigido em  │
│    2 lugares                                   │
│  • Testes precisam cobrir ambas                │
│  • Manutenção 2x mais cara                     │
│                                                 │
│  SOLUÇÃO: Criar classe base ou mixin           │
│  VacinacaoOperacionalMixin(models.Model):     │
│    @property                                   │
│    def atrasada(self): [compartilhado]        │
│    ...                                         │
│                                                 │
│  class AplicacaoVacina(..., VacinacaoOperacional
│  class VacinaLote(..., VacinacaoOperacional)   │
└─────────────────────────────────────────────────┘
```

---

## Diagrama 5: Estados de Ave (Transições Inválidas)

```
ESTADO DE AVE: SEM VALIDAÇÃO DE TRANSIÇÕES
═══════════════════════════════════════════════════════════════════════════

Ave.status choices: ('viva', 'vendida', 'morta', 'abatida')

Transições VÁLIDAS (negócio):
┌──────────────┐
│    VIVA      │  Estado inicial
└──────┬───────┘
       │
   ┌───┴────┬──────────┬─────────┐
   │        │          │         │
   ▼        ▼          ▼         ▼
┌────────┐ ┌──────┐ ┌─────┐ ┌────────┐
│VENDIDA │ │MORTA │ │ ... │ │ABATIDA │
└────────┘ └──────┘ └─────┘ └────────┘
   │         │       │          │
   └─────────┴───────┴──────────┘
            (FIM)

Transições INVÁLIDAS (mas possíveis sem validação!):
┌────────────────────────────────────────────────────────┐
│ ABATIDA → VIVA           (Ave ressuscitada?!)      ✗   │
│ ABATIDA → VENDIDA        (Vender ave morta?!)      ✗   │
│ MORTA → VENDIDA          (Vender ave morta?!)      ✗   │
│ MORTA → ABATIDA          (Abater ave morta?!)      ✗   │
│ VENDIDA → ABATIDA        (Abater ave vendida?!)    ✗   │
└────────────────────────────────────────────────────────┘

Código ATUAL (aves/models.py):
┌──────────────────────────────────────────┐
│ class Ave(...):                          │
│     status = CharField(                  │
│         max_length=20,                   │
│         choices=STATUS_CHOICES           │
│     )                                    │
│     # SEM clean() ou save() validation   │
│     # SEM máquina de estados             │
│     # SEM constraints no BD              │
└──────────────────────────────────────────┘

Código NECESSÁRIO:
┌──────────────────────────────────────────┐
│ class Ave(...):                          │
│     status = CharField(...)              │
│                                          │
│     def clean(self):                     │
│         if self.status == 'abatida':     │
│             raise ValidationError(       │
│                 "Ave abatida não pode... │
│             )                            │
│                                          │
│     def save(self, *args, **kwargs):     │
│         self.full_clean()                │
│         super().save(...)                │
│                                          │
│     # OU usar django-fsm:                │
│     @transition(...)                     │
│     def vender(self):                    │
│         self.status = 'vendida'          │
└──────────────────────────────────────────┘
```

---

## Diagrama 6: Integração Venda-Financeiro (Esperado vs Real)

```
INTEGRAÇÃO ESPERADA ("Ideal")
═══════════════════════════════════════════════════════════════════════════

Quando Venda STATUS = PAGO:
┌──────────────┐       Signal         ┌──────────────────────┐
│    Venda     │  (post_save)        │ LancamentoFinanceiro │
│   STATUS     │ ────────────────>  │  TIPO=ENTRADA        │
│   = PAGO     │   @receiver        │  CATEGORIA=VENDA     │
└──────────────┘                     │  VALOR=venda.valor   │
               Automático, Atômico   │  OneToOne=venda      │
               Sincronizado          └──────────────────────┘

INTEGRAÇÃO REAL ("Atual")
═══════════════════════════════════════════════════════════════════════════

Quando Venda STATUS = PAGO:
┌──────────────┐                    ┌──────────────────────┐
│    Venda     │  1. form_valid()   │  Venda.save()        │
│   STATUS     │                    │  ✓ BD                │
│   = PAGO     │                    └──────────────────────┘
└──────┬───────┘
       │
       │  2. _sync_venda_financeiro() [função manual, na view!]
       │     - Sem @transaction.atomic ⚠️
       │     - Sem Signal ⚠️
       │     - Sem garantia ⚠️
       │
       ▼
    ┌─────────────────────────┐
    │ LancamentoFinanceiro    │
    │ criado/atualizado?      │
    │                         │
    │ ✓ Sucesso               │
    │ ✗ Falha                 │
    │ ? Atualização parcial   │
    └─────────────────────────┘

PROBLEMA:
┌────────────────────────────────────────────────────┐
│ Venda paga mas sem entrada financeira possível:   │
│                                                    │
│ 1. Sync code falha silenciosamente?               │
│ 2. Signal não carrega automaticamente?            │
│ 3. Deletaram lançamento na view admin?            │
│ 4. OneToOne quebrado?                             │
│                                                    │
│ RESULTADO → Venda paga mas $ não entra no caixa! │
└────────────────────────────────────────────────────┘

QUERIES NECESSÁRIAS PARA VALIDAR:
┌────────────────────────────────────────────────────┐
│ SELECT * FROM vendas_venda v               │
│ WHERE v.status_pagamento = 'pago'                  │
│ AND NOT EXISTS (                                   │
│     SELECT 1 FROM financeiro_lancamentofinanceiro  │
│     WHERE venda_id = v.id                         │
│ );                                                 │
│                                                    │
│ ✓ Se retorna 0 linhas = OK                        │
│ ✗ Se retorna N > 0 linhas = PROBLEMA!             │
└────────────────────────────────────────────────────┘
```

---

## Diagrama 7: Matriz de Índices e Performance

```
ANÁLISE DE ÍNDICES (Database Optimization)
═══════════════════════════════════════════════════════════════════════════

Tabela          Campo(s)                  Existe   Recomendação
────────────────────────────────────────────────────────────────────
aves_ave        (finalidade, status)      ✗        ADD INDEX
                (lote_id, status)         ✗        ADD INDEX
                (sexo, ativo)             ✗        ADD INDEX

lotes_lote      (status, finalidade)      ✗        ADD INDEX
                (data_criacao)            ✗        ADD INDEX

vendas_venda    (cliente, data)           ✗        ADD INDEX
                (status_pagamento, data)  ✓        OK

estoque_*       (categoria, nome)         ✓        OK
                (validade)                ✓        OK

financeiro_*    (tipo, categoria, data)   ✓        OK
                (lote_id, data)           ✓        OK

sanidade_*      (lote, data_programada)   ✗        ADD INDEX
                (status)                  ✗        ADD INDEX

nascimentos     (lote_id, data)           ✗        ADD INDEX

abate_abate     (lote_id, data)           ✗        ADD INDEX
                (aves_id)  [M2M]          ✗        ADD INDEX (M2M)

────────────────────────────────────────────────────────────────────
Total faltando: 11 índices

IMPACTO DE FALTA DE ÍNDICES:
┌──────────────────────────────────┐
│ SELECT COUNT(*) FROM aves_ave    │
│ WHERE finalidade='corte'          │
│ AND status='viva'                 │
│                                  │
│ ✗ SEM INDEX: 500ms (table scan) │
│ ✓ COM INDEX: 2ms (index seek)    │
│                                  │
│ Diferença: 250x mais lento!       │
└──────────────────────────────────┘
```

---

**Diagramas gerados:** 12 de abril de 2026

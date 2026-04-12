# Módulo de Reprodutores - Guia de Uso

## Visão Geral

O módulo de **Reprodutores** gerencia a produção genealógica do SISMGC, permitindo:

- **Cadastro de Reprodutores**: Aves designadas para reprodução (matrizes e reprodutores)
- **Gestão de Casais**: Vínculo entre macho e fêmea para produção de filhotes
- **Rastreamento Genético**: Integração com genealogia e qualidade genética
- **Dashboard de Produção**: Visão executiva com indicadores-chave

---

## Estrutura do Módulo

### 1. Reprodutor

Um reprodutor é uma ave dedicada à reprodução, com as seguintes características:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| **Ave** | FK (Ave) | Referência à ave que será reprodutor |
| **Tipo** | Choicefield | `matriz` (♀) ou `reprodutor` (♂) |
| **Status** | Choicefield | `ativo`, `descanso`, `vendido`, `descartado` |
| **Qualidade Genética** | Choicefield | `padrão`, `superior`, `pura` |
| **Valor Estimado** | Decimal | Valor de mercado estimado (R$) |
| **Início Reprodução** | Date | Data quando começou a reproduzir |
| **Fim Reprodução** | Date | Data quando parou de reproduzir |
| **Observações** | Text | Notas sobre o reprodutor |

#### Validações Implementadas:

- ✅ **Tipo deve corresponder ao sexo da ave**: Matriz (♀) só para fêmeas, Reprodutor (♂) só para machos
- ✅ **Finalidade automática**: Ave associada é forçada a ter `finalidade = REPRODUCAO`
- ✅ **Status ativo automático**: Novo reprodutor começa como ATIVO
- ✅ **Índices otimizados**: Busca por `tipo+ativo`, `status`, `qualidade_genetica`

---

### 2. Casal

Um casal agrupa um reprodutor macho com uma matriz fêmea para produção.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| **Reprodutor Macho** | FK (Reprodutor) | Macho do casal |
| **Matriz Fêmea** | FK (Reprodutor) | Fêmea do casal |
| **Data Início** | Date | Quando o casal começou a reproduzir |
| **Data Fim** | Date | Quando o casal foi separado |
| **Status** | Choicefield | `planejado`, `ativo`, `pausado`, `concluído` |
| **Lote** | FK (Lote) | Lote gerado por este casal (opcional) |
| **Observações** | Text | Notas sobre performance reprodutiva |

#### Validações Implementadas:

- ✅ **Macho ≠ Fêmea**: Não permite o mesmo valor para ambos
- ✅ **Tipagem correta**: Reprodutor deve ser macho, Matriz deve ser fêmea
- ✅ **Unicidade**: Mesmo casal não pode ter data_inicio duplicada
- ✅ **Cálculos automáticos**: `duracao_reproducao`, `get_filhotes_count()`
- ✅ **Índices otimizados**: Busca por `status+ativo`, `data_inicio`

---

## Workflows Comuns

### 📋 Workflow 1: Cadastrar novo Reprodutor

1. Acesse **Reprodutores** → **Dashboard**
2. Clique em **"Novo Reprodutor"**
3. Selecione uma **Ave com finalidade REPRODUCAO**
4. Preencha:
   - **Tipo**: Matriz ou Reprodutor
   - **Status**: (será Ativo por padrão)
   - **Qualidade Genética**: Padrão, Superior ou Pura
   - **Valor Estimado**: (opcional)
   - **Data de Início**: Quando começou a reproduzir
5. Clique em **"Cadastrar Reprodutor"**

**Resultado**: 
- Ave é automaticamente forçada a ter `finalidade = REPRODUCAO`
- Reprodutor fica com status ATIVO
- Aparece nas listagens em 24h

---

### 🔗 Workflow 2: Criar um Casal Reprodutivo

1. Acesse **Reprodutores** → **Casais** → **"Novo Casal"**
2. Selecione:
   - **Reprodutor Macho**: Um reprodutor cadastrado ♂
   - **Matriz Fêmea**: Uma matriz cadastrada ♀
3. Preencha:
   - **Data Início**: Quando começam a reproduzir
   - **Status**: Ativo se já estão juntos, Planejado se é futuro
   - **Lote** (opcional): Se já tem lote definido
4. Clique em **"Criar Casal"**

**Resultado**:
- Casal aparece no dashboard
- Filhotes deste casal são automaticamente rastreados via genealogia

---

### 📊 Workflow 3: Acompanhar Desempenho Reprodutivo

1. Acesse **Reprodutores** → **Casais** → Selecione um casal
2. Na **aba de Estatísticas**, veja:
   - **Filhotes Registrados**: Total de filhotes do casal
   - **Últimos Filhotes**: Lista com últimas 5 eclosões
3. Para editar status do casal:
   - Clique em **"Editar"**
   - Mude para **"Pausado"** se está em descanso
   - Mude para **"Concluído"** se foi separado

---

### 🧬 Workflow 4: Vincular com Genealogia

Reprodutores se conectam automaticamente com **Genética**:

- Quando um **Registro Genético** é criado com pai/mãe reprodutores
- Filhotes aparecem em:
  - Página do reprodutor: "Genética Registrada"
  - Página do casal: "Últimos Filhotes"

**Para registrar filhotes**:
1. Acesse **Genética** → **Novo Registro Genético**
2. Selecione:
   - **Filho**: Ave nascida (lote)
   - **Pai**: Reprodutor macho
   - **Mãe**: Matriz fêmea
3. O vínculo aparece automaticamente

---

## Dashboard de Reprodução

Acesso em: **Reprodutores** → **Dashboard**

### Indicadores Resumitivos

```
┌─────────────────┬──────────────┬──────────────┬──────────────┐
│ Total           │ Casais       │ Casais       │ Qualidade    │
│ Reprodutores    │ Registrados  │ Ativos       │ SUPERIOR     │
└─────────────────┴──────────────┴──────────────┴──────────────┘
```

### Abas do Dashboard

| Aba | Conteúdo |
|-----|----------|
| **Reprodutores Destacados** | Top 5 reprodutores ♂ com qualidade superior e mais casais ativos |
| **Matrizes Destacadas** | Top 5 matrizes ♀ com qualidade superior e mais casais ativos |
| **Casais em Produção** | Últimos 30 dias de casais com filtro por status |

---

## Permissões e Controle de Acesso

O módulo respeita os papéis do sistema:

| Permissão | Admin | Gerente | Funcionário |
|-----------|-------|---------|-------------|
| **Ver reprodutores** | ✅ | ✅ | ❌ |
| **Cadastrar reprodutor** | ✅ | ✅ | ❌ |
| **Editar reprodutor** | ✅ | ✅ | ❌ |
| **Deletar reprodutor** | ✅ | ❌ | ❌ |
| **Ver casais** | ✅ | ✅ | ❌ |
| **Criar casal** | ✅ | ✅ | ❌ |

---

## Integrações com Outros Módulos

### 🐔 Aves
- Cada reprodutor é uma Ave
- Ave é forçada para `finalidade = REPRODUCAO`
- Genealogia de Ave é consultável

### 🧬 Genética
- Filhotes são registrados via `RegistroGenetico`
- Pai/Mãe são reprodutores
- Rastreamento automático de descendentes

### 📦 Lotes
- Casais podem gerar um lote
- Lote pode ser vinculado ao casal para rastreamento de origem

### 🏠 Linhagens
- Reprodutor herda linhagem da ave
- Filtro por linhagem na listagem

---

## Buscas e Filtros

### Lista de Reprodutores

```
Filtros Disponíveis:
├─ Busca: Código interno ou nome da ave
├─ Tipo: Matriz (♀) ou Reprodutor (♂)
├─ Status: Ativo, Descanso, Vendido, Descartado
├─ Qualidade: Padrão, Superior, Pura
└─ Ordernar por: Código, Data cadastro
```

### Lista de Casais

```
Filtros Disponíveis:
├─ Status: Planejado, Ativo, Pausado, Concluído
├─ Lote: Filtrar por lote gerado
├─ Data: Últimos 30/60/90 dias
└─ Ordernar por: Data mais recente
```

---

## Modelos de Dados

### Reprodutor

```python
class Reprodutor(TimeStampedModel, AtivoInativoModel, AuditModel):
    ave = OneToOneField(Ave)
    tipo = CharField(choices=TIPOS)  # matriz, reprodutor
    status = CharField(choices=STATUS_CHOICES)  # ativo, descanso, vendido, descartado
    qualidade_genetica = CharField(choices=QUALIDADE_CHOICES)  # padrao, superior, pura
    valor_estimado = DecimalField(max_digits=10, decimal_places=2)
    data_inicio_reproducao = DateField()
    data_fim_reproducao = DateField(null=True)
    observacoes = TextField(blank=True)

    class Meta:
        indexes = [
            Index(fields=["tipo", "ativo"]),
            Index(fields=["status"]),
            Index(fields=["qualidade_genetica"]),
        ]
```

### Casal

```python
class Casal(TimeStampedModel, AtivoInativoModel, AuditModel):
    reprodutor_macho = ForeignKey(Reprodutor, related_name="casais_como_macho")
    matriz_femea = ForeignKey(Reprodutor, related_name="casais_como_femea")
    data_inicio = DateField()
    data_fim = DateField(null=True)
    status = CharField(choices=STATUS_CHOICES)  # planejado, ativo, pausado, concluido
    lote = ForeignKey(Lote, null=True, blank=True)
    observacoes = TextField(blank=True)

    class Meta:
        unique_together = [["reprodutor_macho", "matriz_femea", "data_inicio"]]
        indexes = [
            Index(fields=["status", "ativo"]),
            Index(fields=["data_inicio"]),
        ]
```

---

## URLs e Rotas

```
/reprodutores/                           → Dashboard
/reprodutores/reprodutores/              → Lista de reprodutores
/reprodutores/reprodutores/novo/         → Criar reprodutor
/reprodutores/reprodutores/<id>/         → Detalhe reprodutor
/reprodutores/reprodutores/<id>/editar/  → Editar reprodutor
/reprodutores/reprodutores/<id>/excluir/ → Deletar reprodutor

/reprodutores/casais/                    → Lista de casais
/reprodutores/casais/novo/               → Criar casal
/reprodutores/casais/<id>/               → Detalhe casal
/reprodutores/casais/<id>/editar/        → Editar casal
/reprodutores/casais/<id>/excluir/       → Deletar casal
```

---

## Dicas e Boas Práticas

### ✅ DO (Recomendado)

- ✅ Usar `status = DESCANSO` para reprodutores em repouso (melhor que excluir)
- ✅ Registrar `qualidade_genetica` para filtragem posterior
- ✅ Vincular lote ao casal para rastreamento de origem
- ✅ Usar observações para anotar comportamentos reprodutivos
- ✅ Consultar dashboard antes de cruzamentos para avaliar saúde genética

### ❌ DON'T (Evitar)

- ❌ Deletar reprodutores ativos (histórico perdido)
- ❌ Esquecer de vincular cavalo com ave finalidade REPRODUCAO
- ❌ Criar casais com mesma ave para macho e fêmea
- ❌ Não registrar filhotes em Genética (quebra rastreamento)
- ❌ Deixar `data_fim` vazia para casais já separados

---

## Troubleshooting

### ❓ "Ave deve ter finalidade REPRODUCAO"

**Problema**: Ao criar reprodutor, erro diz que ave precisa de outra finalidade

**Solução**:
1. Acesse **Aves** → Lista
2. Encontre a ave
3. Clique em **Editar**
4. Mude **Finalidade** para **REPRODUCAO**
5. Tente criar reprodutor novamente

---

### ❓ "Não posso criar casal com mesma ave"

**Problema**: Sistema rejeita casal quando macho = fêmea

**Solução**: 
- Isso é por design para evitar consanguinidade
- Selecione aves diferentes para reprodutor e matriz

---

### ❓ "Filhotes não aparecem no casal"

**Problema**: Criei casal mas filhotes não aparecem

**Solução**:
1. Acesse **Genética** → Novo Registro
2. Crie um registro vinculando filho com pai/mãe do casal
3. Volte para detalhe do casal
4. Filhotes agora aparecem em "Últimos Filhotes"

---

## Performance e Índices

O módulo está otimizado com índices em campos críticos:

```sql
-- Reprodutor
INDEX repr_tipo_ativo_idx ON reprodutor(tipo, ativo)
INDEX repr_status_idx ON reprodutor(status)

-- Casal
INDEX casal_status_ativo_idx ON casal(status, ativo)
INDEX casal_data_inicio_idx ON casal(data_inicio)
```

Isso garante listagens rápidas mesmo com milhares de registros.

---

## Próximas Funcionalidades Planejadas

- [ ] Cálculo automático de inbreeding (consanguinidade)
- [ ] Relatório de produtividade por casal
- [ ] Alertas de quando separar casais (ciclo reprodutivo)
- [ ] Integração com sanidade (status de vacinação)
- [ ] Exportação de genealogias em formato PDF
- [ ] Gráficos de tendência genética temporal

---

## Suporte e Documentação

Para dúvidas:
1. Consulte este guia
2. Acesse o dashboard em **Reprodutores**
3. Contate o administrador do sistema

**Versão**: 1.0 | **Última atualização**: 2026-03-28 | **Sistema**: SISMGC

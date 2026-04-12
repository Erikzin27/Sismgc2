"""
INTEGRAÇÃO VENDAS ↔ FINANCEIRO - GUIA DE TESTE E USO

Este arquivo documenta como a integração funciona e como testar.
"""

# ========================================
# 1. VISÃO GERAL
# ========================================

A integração entre Vendas e Financeiro agora funciona da seguinte forma:

ANTES (sem integração):
  - Usuário criava venda em "Vendas"
  - Usuário TINHA QUE criar entrada manualmente em "Financeiro"
  - Risco: duplicidade, inconsistência, esquecimento

DEPOIS (com integração):
  - Usuário cria venda em "Vendas"
  - Sistema AUTOMATICAMENTE cria entrada em "Financeiro"
  - Se alterar venda: entrada também é atualizada
  - Se deletar venda: entrada é deletada

# ========================================
# 2. REGRAS DE NEGÓCIO
# ========================================

CRIAÇÃO:
  Ao criar venda com status "Pago":
  ✓ Sistema cria entrada no Financeiro automaticamente
  ✓ Categoria = "Venda"
  ✓ Tipo = "Entrada"
  ✓ Valor = valor_total da venda
  ✓ Descrição = "Venda: [produto] - Cliente: [cliente]"
  ✓ Forma pagamento = copia da venda
  ✓ Vincula via OneToOneField

EDITAÇÃO:
  Ao editar venda paga:
  ✓ Atualiza entrada vinculada (data, valor, descricao, etc)
  ✓ Mantém FK intacta
  ✓ Sem duplicidade (OneToOneField)

  Ao marcar venda como "Não paga":
  ✓ Remove entrada do financeiro
  ✓ Mantém auditoria nos logs

EXCLUSÃO:
  Ao deletar venda paga:
  ✓ Remove entrada do financeiro também
  ✓ Cascada automática
  ✓ Log registra tudo

# ========================================
# 3. COMO TESTAR
# ========================================

## TESTE 1: Nova Venda Paga

URL: http://localhost:8000/vendas/create/

1. Preencher:
   - Data: 01/04/2026
   - Cliente: João Silva
   - Produto: Ovos Frescos
   - Categoria: Ovos
   - Quantidade: 10
   - Unidade: dz (dúzia)
   - Valor Unitário: 15,00
   - Status Pagamento: ✓ Pago
   - Forma: Pix

2. Salvar

3. Resultado esperado:
   ✓ Mensagem: "Venda criada e entrada financeira gerada com sucesso"
   ✓ Redireciona para lista de vendas

4. Verificar:
   a) Vendas > Lista > Coluna "Financeiro": deve mostrar "Entrada gerada" (verde)
   b) Financeiro > Lista > Filtrar por "Origem: Venda": deve aparecer a entrada
   c) Financeiro > Detalhe > "Venda Vinculada": mostra link para venda


## TESTE 2: Nova Venda Pendente

URL: http://localhost:8000/vendas/create/

1. Preencher igual à anterior, mas:
   - Status Pagamento: Pendente

2. Salvar

3. Resultado esperado:
   ✓ Mensagem: "Venda criada com sucesso"
   ✓ Coluna "Financeiro": "Sem entrada" (cinza)

4. Verificar:
   - NÃO deve criar entrada no financeiro
   - Quando mudar para "Pago", vai criar entrada automaticamente


## TESTE 3: Editar Venda Paga

1. Ir na venda criada em TESTE 1
2. Clicar "Editar"
3. Mudar:
   - Valor Unitário: 20,00
   - Forma: Crédito

4. Salvar

5. Resultado esperado:
   ✓ Mensagem: "Venda atualizada e entrada financeira sincronizada"
   ✓ Ir ao Financeiro e conferir:
     - Valor atualizado para novo total
     - Forma de pagamento updated
     - Descrição reflete mudança

## TESTE 4: Marcar Venda como Pendente

1. Ir na venda paga com entrada
2. Editar
3. Mudar Status para "Pendente"
4. Salvar

5. Resultado esperado:
   ✓ Mensagem: "Venda atualizada"
   ✓ Coluna Financeiro: "Sem entrada" (cinza)
   ✓ Ir ao Financeiro: entrada foi deletada

## TESTE 5: Deletar Venda com Entrada

1. Ir numa venda paga
2. Clicar "Excluir"
3. Confirmar

4. Resultado esperado:
   ✓ Mensagem: "Venda excluída. Lançamento financeiro #123 também removido"
   ✓ Venda some da lista
   ✓ Ir ao Financeiro: entrada foi deletada

## TESTE 6: Sincronização Manual (Admin)

1. Ir para Django Admin: http://localhost:8000/admin/
2. Vendas > Vendas
3. Selecionar múltiplas vendas pagas
4. Ação: "Sincronizar com financeiro agora"
5. Clicar "Ir"

6. Resultado esperado:
   ✓ Mensagem de sucesso com número de vendas sincronizadas

# ========================================
# 4. VERIFICAR LOGS
# ========================================

Abrir logs para auditoria:

Windows:
  Arquivos de log estão em: <PROJETO>/logs/

Comando:
  grep "Vendas:" <PROJETO>/logs/app.log | tail -50

Exemplos de logs:
  INFO: "Vendas: Venda #123 - novo lançamento financeiro #456 criado"
  INFO: "Vendas: Venda #123 - lançamento financeiro #456 atualizado"
  INFO: "Vendas: Venda #123 - lançamento financeiro #456 removido (venda não está paga)"
  ERROR: "Vendas: Venda #123 - ERRO ao sincronizar com financeiro: ..."

# ========================================
# 5. DASHBOARD / RELATÓRIOS
# ========================================

Verificar impacto no Dashboard:

Vendas > Lista > Resumo (no topo)
  ✓ Total de vendas
  ✓ Total em valor
  ✓ Vendas pagas
  ✓ Vendas pendentes
  ✓ Vendas com entrada no financeiro ("Com entrada")

Financeiro > Lista > Resumo
  ✓ Entradas (inclui vendas)
  ✓ Saídas
  ✓ Saldo
  ✓ Total vinculados a vendas

Financeiro > Dashboard
  ✓ Entradas visuais incluem vendas
  ✓ Fluxo de caixa com vendas

# ========================================
# 6. TRATAMENTO DE ERROS
# ========================================

Cenários e como lidar:

ERRO: "Múltiplos lançamentos encontrados"
  Causa: Inconsistência no banco (muito raro)
  Ação: Verificar logs, contactar admin
  Fix: Limpar manualmente via admin

ERRO: "Erro ao sincronizar com financeiro"
  Causa: Erro genérico no processo
  Ação: Venda foi salva, mas entrada não
  Fix: Tentar novamente, consultar logs
  
AVISO: "Venda atualizada, entrada pendente"
  Causa: Venda foi salva mas entrada falhou
  Ação: Clicar novamente "Editar > Salvar"
  Fix: Botão "Sincronizar com financeiro agora" no admin

# ========================================
# 7. PROPRIEDADES E MÉTODOS ÚTEIS
# ========================================

Em Venda:
  venda.tem_entrada_financeira
    → True se tem lançamento vinculado
    → False caso contrário

  venda.status_integracao
    → 'vinculada': venda paga + entrada no financeiro
    → 'pendente_vínculo': paga mas ainda sem entrada
    → 'não_sincronizada': venda não paga

  venda.get_status_integracao_display()
    → String legível do status

Em LancamentoFinanceiro:
  lancamento.venda
    → Referência para venda (se houver)
    → None se for lançamento manual

  lancamento.is_from_venda
    → Propriedade read-only mostrando se veio de venda

# ========================================
# 8. TROUBLESHOOTING
# ========================================

Problema: Entrada não aparece depois de criar venda paga
Solução:
  1. Recarregar página
  2. Verifique em Financeiro > Filtro "Origem: Venda"
  3. Verifique logs para erros
  4. Se persistir: sincronizar manualmente via admin

Problema: Entrada não foi deletada ao excluir venda
Solução:
  1. Verifique se venda realmente foi deletada
  2. Buscar entrada em Financeiro manualmente
  3. Deletar manualmente se encontrar órfã

Problema: Valores não batem
Solução:
  1. Editar venda: desconto está incluído?
  2. Verificar se forma pagamento é diferente
  3. Verificar observações (pode ter info extra)

# ========================================
# 9. CÓDIGO E ARQUIVOS
# ========================================

Principais arquivos alterados:

vendas/signals.py (NOVO)
  - Sincronização automática via signals
  
vendas/models.py
  - Propriedades: tem_entrada_financeira, status_integracao
  - Métodos display
  
vendas/apps.py
  - ready() método registra signals

vendas/views.py
  - _sync_venda_financeiro() melhorada com logging
  - Create/Update/Delete com melhor tratamento

vendas/admin.py
  - Admin com vínculo visual
  - Ação para sincronizar manualmente

financeiro/admin.py
  - Mostra origem (venda/manual)
  - Link para venda

# ========================================
# 10. PERFORMANCE
# ========================================

Otimizações já aplicadas:

- OneToOneField: evita duplicidade, FK única
- select_related: carrega venda quando lista financeiro
- Índice: fields=["venda"] em LancamentoFinanceiro
- Logging sem overhead
- Sem queries N+1

# ========================================
# 11. NEXT STEPS (FUTURAS MELHORIAS)
# ========================================

Se quiser expandir a integração:

1. Webhook para webhooks de pagamento (Pix, boleto)
2. Reconciliação automática ao confirmar pagamento
3. Relatório "Vendas com Atraso"
4. Dashboard com gráficos de vendas vs entradas
5. Exportação (CSV, PDF) com dados sincronizados
6. Integração com sistemas de nota fiscal

# ========================================
"""

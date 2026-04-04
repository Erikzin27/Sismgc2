# Matriz de Permissoes e Visibilidade - SISMGC

## Perfis por modulo

| Modulo / Area | Admin | Gerente | Funcionario |
|---|---|---|---|
| Dashboard geral | Sim | Sim | Sim |
| Aves | Sim | Sim | Se tiver permissao |
| Lotes | Sim | Sim | Se tiver permissao |
| Linhagens | Sim | Sim | Se tiver permissao |
| Incubacao | Sim | Sim | Se tiver permissao |
| Nascimentos | Sim | Sim | Se tiver permissao |
| Estoque | Sim | Sim | Se tiver permissao |
| Sanidade | Sim | Sim | Se tiver permissao |
| Abate | Sim | Sim | Se tiver permissao |
| Vendas | Sim | Sim | Se tiver permissao |
| Financeiro | Sim | Sim | Se tiver permissao |
| Planejamento | Sim | Sim | Se tiver permissao |
| Relatorios | Sim | Sim | Nao |
| Historico | Sim | Sim | Nao |
| Usuarios | Sim | Sim, conforme permissao | Se tiver permissao |
| Area Admin | Sim | Nao | Nao |
| Configuracoes | Sim | Nao | Nao |

## Abas sensiveis em detalhes

| Tela | Aba | Admin | Gerente | Funcionario |
|---|---|---|---|---|
| Ave | Historico | Sim | Sim | Nao |
| Ave | Sanidade | Sim | Sim | Se tiver permissao |
| Ave | Vendas | Sim | Sim | Se tiver permissao |
| Ave | Abates | Sim | Sim | Se tiver permissao |
| Lote | Historico | Sim | Sim | Nao |
| Lote | Sanidade | Sim | Sim | Se tiver permissao |
| Lote | Vendas | Sim | Sim | Se tiver permissao |
| Lote | Abates | Sim | Sim | Se tiver permissao |
| Lote | Incubacao | Sim | Sim | Se tiver permissao |
| Lote | Movimentacoes | Sim | Sim | Se tiver permissao |

## Links cruzados entre modulos

| Link cruzado | Regra |
|---|---|
| Venda -> lancamento financeiro | So vira link se puder ver financeiro |
| Lancamento financeiro -> venda | So vira link se puder ver vendas |
| Busca global -> venda | So aparece se puder ver vendas |
| Busca global -> ave/lote/linhagem/incubacao | So aparece se puder ver o modulo |
| Calendario -> vendas | So aparece se puder ver vendas |
| Calendario -> pagamentos | So aparece se puder ver financeiro |
| Calendario -> planejamento | So aparece se puder ver planejamento |

## Acoes por permissao

- `Novo` -> so com permissao `add_*`
- `Editar` -> so com permissao `change_*`
- `Excluir` -> so com permissao `delete_*`
- exportacoes -> so para perfil/modulo autorizado

## Regra pratica

- `admin`: visao total
- `gerente`: visao gerencial e operacional ampla
- `funcionario`: so ve o que a permissao real liberar
- A interface deve permanecer coerente em:
  - menu
  - dashboard
  - listagem
  - detalhe
  - abas
  - busca
  - calendario
  - links cruzados

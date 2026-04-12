# 🧪 GUIA DE TESTES - MODERNIZAÇÃO FINANCEIRO

**Data**: 11 de abril de 2026  
**Tempo Estimado**: 15-20 minutos  
**Checklist**: 40+ testes

---

## 🚀PARA COMEÇAR

```bash
cd "c:\Users\Erik C. Oliveira\Desktop\Workspace\MGC-GR"
python manage.py runserver 0.0.0.0:8000

# Acesse: http://localhost:8000/financeiro/
```

---

## 📱 TESTE 1: MOBILE (XS - até 576px)

### Abrir DevTools
```
F12 → Ctrl+Shift+M → Selecione "iPhone SE"
```

### Testes de Layout
- [ ] **Header**: Ações em coluna (+ Novo acima)
- [ ] **Filtros**: Busca + Tipo visíveis, outros ocultos
- [ ] **Cards Resumo**: 1 column stacked
- [ ] **Lista**: Cards mobile, não tabela
- [ ] **Botões**: Ocupam 100% width
- [ ] **Badges**: Aparecem corretamente
- [ ] **Sem horizontal scroll**: Tudo cabe na tela

### Testes de Interação
- [ ] **Buscar**: Digite "ração" → Filtra cards
- [ ] **Tipo**: Selecione "Entrada" → Apenas entradas
- [ ] **Clique Card**: Abre detail page
- [ ] **Botão Ver**: Funciona
- [ ] **Botão Editar**: Abre form
- [ ] **Botão Excluir**: Abre confirm
- [ ] **Download**: Arquivo baixa (se existir)

### Testes de Visual
- [ ] **Cards**: Sombras visíveis
- [ ] **Cores**: Verde entrada, vermelho saída
- [ ] **Badges Venda**: Azul com ícone 🛒
- [ ] **Badges Manual**: Cinza com ícone ✏️
- [ ] **Valores**: Amarela à direita

---

## 📱 TESTE 2: TABLET PEQUENO (SM - 576px-768px)

### Resize
```
DevTools → Selecione "Galaxy Tab" (800px)
```

### Testes
- [ ] **Filtros**: Começam a aparecer opcoes secundarias
- [ ] **Cards**: Ainda 1 coluna
- [ ] **Lista Items**: Cards OK
- [ ] **Buttons**: Touch-friendly ainda

---

## 📱 TESTE 3: TABLET GRANDE / LAPTOP (MD - 768px-992px)

### Resize
```
DevTools → Width = 850px
```

### Testes
- [ ] **Filtros Secundários**: Categoria, Origem, Datas aparecem
- [ ] **Layout**: Mais compacto, menos espaço
- [ ] **Cards**: Ainda mobile cards
- [ ] **Buttons**: Bem distribuídos

---

## 📱 TESTE 4: LAPTOP (LG - 992px-1200px)

### Resize
```
Width = 1100px
```

### Testes
- [ ] **Filtros**: Todos visíveis inline
- [ ] **Cards**: Resposivos (3 columns)
- [ ] **Lista**: Ainda cards (não tabela yet)
- [ ] **Visual**: Bem espaçado

---

## 🖥️ TESTE 5: DESKTOP (XL - 1200px+)

### Resize Full Screen ou 1920px

### Testes de Layout
- [ ] **Filtros**: Todos inline, compactos
- [ ] **Cards Resumo**: 3 colunas lado a lado
- [ ] **Tabela**: Substitui cards
- [ ] **Colunas Tabela**:
  - [ ] Data (esquerda)
  - [ ] Tipo (badge)
  - [ ] Categoria
  - [ ] Descrição
  - [ ] Pagamento
  - [ ] Origem (badge)
  - [ ] Valor (direita, colorido)
  - [ ] Download (center)
  - [ ] Ações (direita)
- [ ] **Sem horizontal scroll**: Tudo cabe

### Testes de Interação
- [ ] **Hover Linha**: Background muda (subtle)
- [ ] **Hover Buttons**: Transform suave
- [ ] **Links**: Funcionam
- [ ] **Paginação**: Apareça se > 20 registros

### Testes de Visual
- [ ] **Header Table**: Fundo azul-claro, uppercase
- [ ] **Badges**: Cores corretas
- [ ] **Valores**: Coloridos (verde entrada, vermelho saída)
- [ ] **Ícones**: Todos aparecem

---

## 🎨 TESTE 6: TEMA ESCURO (Padrão)

### Verificar Automaticamente

### Testes
- [ ] **Background**: Azul escuro (#0e1424)
- [ ] **Texto**: Branco-azulado (#e5ecff)
- [ ] **Cards**: Azul escuro com border sutil
- [ ] **Tabela**: Header azul-claro
- [ ] **Badges**: Visíveis e contrastadas
- [ ] **Links**: Azul (#7db3ff)
- [ ] **Hover**: Sombra azulada

---

## 🌓 TESTE 7: TEMA CLARO

### Ativar Tema Claro
```
Dashboard → Tema → Claro (se disponível)
ou
Chrome Dev Tools → Rendering → Emulate CSS media "prefers-color-scheme" → light
```

### Testes
- [ ] **Background**: Branco/cinza claro
- [ ] **Texto**: Preto/cinza escuro
- [ ] **Cards**: Branco com border cinza
- [ ] **Tabela**: Header cinza claro
- [ ] **Badges**: Visíveis
- [ ] **Links**: Azul escuro
- [ ] **Contraste**: Tudo legível

---

## 🔍 TESTE 8: FILTROS FUNCIONAMENTO

### Teste Busca
- [ ] Digite "ração" → Filtra por descrição
- [ ] Observe: HTMX carregando, página atualiza
- [ ] Limpar: Voltar ao normal

### Teste Tipo
- [ ] Selecione "Entrada" → Apenas entradas
- [ ] Cards resumo atualizam
- [ ] Tabela/cards atualizam
- [ ] Mudar para "Saída" → Apenas saídas
- [ ] Total de registros muda

### Teste Categoria (MD+)
- [ ] Selecione "Ração" → Filtra
- [ ] Volte todos → Unfilter

### Teste Origem (MD+)
- [ ] "Venda" → Apenas vinculadas
- [ ] "Manual" → Apenas manuais
- [ ] Counts atualizam

### Teste Data (MD+)
- [ ] Data Início → Filtra desde data
- [ ] Data Fim → Filtra até data
- [ ] Ambas → Range de período

### Teste Limpar
- [ ] Clique "Limpar" → Reset all
- [ ] Valores voltam ao normal

---

## 📊 TESTE 9: CARDS RESUMO

### Entradas
- [ ] Valor correto (soma filtro)
- [ ] Ícone verde presente
- [ ] "Receitas do período"

### Saídas
- [ ] Valor correto
- [ ] Ícone vermelho
- [ ] "Despesas do período"

### Saldo
- [ ] = Entradas - Saídas
- [ ] Ícone azul
- [ ] "Resultado atual"

### Responsividade
- [ ] Mobile: 1 card por linha
- [ ] Tablet: 2 cards por linha
- [ ] Desktop: 3 cards por linha

---

## 📋 TESTE 10: DESKTOP TABELA

### Colunas Presentes
- [ ] Data (clicável)
- [ ] Tipo (badge verde/vermelho)
- [ ] Categoria
- [ ] Descrição (truncado)
- [ ] Pagamento
- [ ] Origem (badge azul/cinza)
- [ ] Valor (colorido)
- [ ] Download (icon)
- [ ] Ações (3 buttons)

### Comportamento Linhas
- [ ] Hover: Background muda
- [ ] Clique Data: Abre detail
- [ ] Clique Desc: Nada (apenas link title)

### Buttons Ações
- [ ] Ver: Detail page ✅
- [ ] Editar: Edit form ✅
- [ ] Excluir: Confirm delete ✅

---

## 📱 TESTE 11: MOBILE CARDS

### Card Header
- [ ] Título (clicável)
- [ ] Data + Categoria em meta
- [ ] Badge Tipo (Entrada/Saída) à direita
- [ ] Separador linha

### Card Body (2-col grid)
- [ ] **Linha 1**: Valor (grande, colorido) + Pagamento
- [ ] **Linha 2**: Origem (badge) + Arquivo (link)
- [ ] Sub-labels uppercase
- [ ] Valores corretos

### Card Actions
- [ ] Ver: Funciona
- [ ] Editar: Funciona
- [ ] Excluir: Funciona
- [ ] Botões distribuídos uniformemente

### Visual Card
- [ ] Sombra presente
- [ ] Borders arredondados
- [ ] Espaçamento interno correto
- [ ] Cores badges corretas

---

## 🔗 TESTE 12: INTEGRAÇÃO VENDAS

### Desktop Quando Vinculada
- [ ] Descrição têm "Venda #123"
- [ ] Origem mostra "🛒 Venda"
- [ ] Cor azul

### Mobile Quando Vinculada
- [ ] Meta mostra "Venda #123"
- [ ] Card field "Origem": "🛒 Venda #123"
- [ ] Cor azul indicator

### Quando Manual
- [ ] Desktop: "✏️ Manual"
- [ ] Mobile: "✏️ Manual"
- [ ] Cor cinza

---

## 📥 TESTE 13: DOWNLOADS/LINKS

### Quando Arquivo Existe
- [ ] Desktop: Icon clicável
- [ ] Mobile: "Download" text
- [ ] Clique: Abre/baixa arquivo

### Quando Sem Arquivo
- [ ] Desktop: Tracejado "—"
- [ ] Mobile: "Sem arquivo"
- [ ] Cinza/opaco

---

## 📄 TESTE 14: PAGINAÇÃO

### Se > 20 registros
- [ ] Aparece ao final
- [ ] Links funcionam
- [ ] Próximo/Anterior navegam
- [ ] Números de página
- [ ] Current page destacado

### Responsividade
- [ ] Mobile: Compacto
- [ ] Desktop: Espaçado

---

## 🎯 TESTE 15: BADGES & CORES

### Badges Tipo
- [ ] **Entrada**: Verde #1fbf91 + ✅
- [ ] **Saída**: Vermelho #dc3545 + ❌

### Badges Origem
- [ ] **Venda**: Azul #0d6efd + 🛒
- [ ] **Manual**: Cinza #6c757d + ✏️

### Valores
- [ ] **Entrada**: Verde (colorido)
- [ ] **Saída**: Vermelho (colorido)

---

## ⚡ TESTE 16: PERFORMANCE

### Load Time
- [ ] Página carrega < 1s
- [ ] HTMX requests < 500ms
- [ ] Smooth scrolling

### Sem Issues
- [ ] Memory não pula
- [ ] CPU < 10%
- [ ] Sem jank/delays

---

## 🔒 TESTE 17: PERMISSÕES

### Se User = Visualizador
- [ ] Botão Editar: Escondido
- [ ] Botão Excluir: Escondido
- [ ] Apenas Ver: Visível

### Se User = Editor
- [ ] Ver: Visível
- [ ] Editar: Visível
- [ ] Excluir: Escondido

### Se User = Admin
- [ ] Todos buttons: Visíveis

---

## 🖱️ TESTE 18: ACESSIBILIDADE

### Keyboard Navigation
- [ ] Tab: Navega buttons
- [ ] Enter: Ativa botão
- [ ] Arrow Down/Up: Qualquer menu
- [ ] Esc: Fecha modal

### Screen Reader
- [ ] Alt texto em icons
- [ ] Labels associados
- [ ] ARIA attributes presentes

---

## ✅ TESTE FINAL CHECKLIST

| Teste | Status | Notas |
|-------|--------|-------|
| Mobile <576px | ☐ PASS | |
| Tablet SM 576px | ☐ PASS | |
| Tablet MD 768px | ☐ PASS | |
| Laptop LG 992px | ☐ PASS | |
| Desktop XL 1200px | ☐ PASS | |
| Desktop 2XL 1400px | ☐ PASS | |
| Tema Escuro | ☐ PASS | |
| Tema Claro | ☐ PASS | |
| Filtros | ☐ PASS | |
| Cards Resumo | ☐ PASS | |
| Tabela Desktop | ☐ PASS | |
| Cards Mobile | ☐ PASS | |
| Badges | ☐ PASS | |
| Links/Actions | ☐ PASS | |
| Performance | ☐ PASS | |
| Permissões | ☐ PASS | |
| Acessibilidade | ☐ PASS | |
| Dados Intactos | ☐ PASS | |
| Backend OK | ☐ PASS | |
| **RESULTADO FINAL** | ☐ **PASS** | |

---

## 🎬 DEMONSTRAÇÃO RÁPIDA (5 min)

1. **Mobile** (1 min)
   - Abra DevTools
   - Selecione iPhone
   - Scroll pelos cards
   - Teste um filtro

2. **Desktop** (2 min)
   - Full screen
   - Observe tabela
   - Hover um valor
   - Clique "Editar"

3. **Tema** (1 min)
   - Alterne claro/escuro
   - Veja cores mudar
   - Contraste > 4.5:1

4. **Filtros** (1 min)
   - Digite busca
   - Selecione tipo
   - Vea cards atualizar

---

## 📋 RESULTADO ESPERADO

Você deve ver:

✅ **Layout Premium**
- Cards resumo coloridos
- Filtros modernos
- Badges visuais

✅ **Responsividade Perfeita**
- Mobile: Cards elegantes
- Desktop: Tabela moderna
- Sem scroll horiz

✅ **Performance**
- Carrega rápido
- Smooth scrolling
- Sem delays

✅ **Dados**
- Todos lançamentos visíveis
- Filtros funcionam
- Links corretos

✅ **Tema**
- Escuro original funciona
- Claro com contraste ok
- Colors corretas

---

## 🆘 Se Algo Não Funcionar

### Problema: Cards não aparecem
```
1. Abra DevTools (F12)
2. Console aba
3. Procure por erros (vermelho)
4. Hard refresh: Ctrl+Shift+R
```

### Problema: Filtros não atualizam
```
1. Verifique se HTMX está carregando
2. Check Console para erros
3. Verifique network (XHR requests)
4. Teste outro browser
```

### Problema: Tema não muda
```
1. Limpe cache: Ctrl+Shift+Delete
2. Verifique data-bs-theme attribute
3. Reload página: Ctrl+R
```

### Problema: Desktop tabela não aparece
```
1. Maximize window (XL breakpoint)
2. ou use DevTools para force 1200px
3. Table deve aparecer automaticamente
```

---

## 📞 CONCLUSÃO

Se todos os testes ✅ PASS:

### 🎉 SUCESSO!

Financeiro foi modernizado com sucesso.

Layout é premium, responsivo e funcional.

Pronto para produção em:

```
http://localhost:8000/financeiro/
```

---

**Happy Testing! 🧪✨**

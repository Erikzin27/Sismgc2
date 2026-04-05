# SISMGC

Sistema Inteligente de Gestao de Granja e Controle Avicola.

Projeto web desenvolvido com Django para apoiar a operacao diaria de granjas, com foco em controle zootecnico, financeiro, sanidade, estoque, reproducao, historico e relatorios.

## Visao geral

O SISMGC foi estruturado para uso local e em rede local, mantendo simplicidade de implantacao com SQLite e interface baseada em Django Templates + Bootstrap 5.

Hoje o sistema ja cobre fluxos importantes como:

- dashboard operacional
- controle de aves e lotes
- linhagens e genetica
- incubacao e nascimentos
- estoque e alimentacao
- sanidade e carencia
- abate e vendas
- financeiro real e planejamento futuro
- relatorios, historico e calendario
- controle de usuarios, perfis e permissoes

## Funcionalidades principais

- Controle completo de aves, lotes e linhagens em uma unica base
- Gestao operacional da granja com foco em rotina diaria e tomada de decisao
- Registro de incubacao, nascimentos, reproducao e historico zootecnico
- Controle de estoque, alimentacao, sanidade e carencia sanitaria
- Vendas integradas ao financeiro de forma segura
- Dashboard com indicadores, alertas e visao rapida da operacao
- Relatorios gerenciais para acompanhamento tecnico e financeiro
- Calendario operacional com eventos importantes da granja
- Controle de usuarios, perfis e permissoes por nivel de acesso
- Estrutura preparada para crescimento futuro sem abandonar a base atual

## Stack

- Python 3.13
- Django 6
- Django REST Framework
- SQLite
- Bootstrap 5
- OpenPyXL
- Pillow
- ReportLab
- WeasyPrint

## Modulos do sistema

- Dashboard
- Linhagens
- Aves
- Lotes
- Genetica
- Incubacao
- Nascimentos
- Estoque
- Alimentacao
- Sanidade
- Abate
- Vendas
- Financeiro
- Relatorios
- Historico
- Usuarios
- Calendario
- Configuracoes

## Como executar localmente

### 1. Clonar o repositorio

```bash
git clone https://github.com/Erikzin27/Sismgc2.git
cd Sismgc2
```

### 2. Criar e ativar a virtualenv

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as dependencias

```bash
pip install -r requirements.txt
```

### 4. Criar o arquivo `.env`

Crie um arquivo `.env` na raiz do projeto com base no `.env.example`.

Exemplo:

```env
SECRET_KEY=sua-chave-aqui
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0
```

### 5. Aplicar as migrations

```bash
python manage.py migrate
```

### 6. Executar o servidor

```bash
python manage.py runserver
```

Para acesso em rede local:

```bash
python manage.py runserver 0.0.0.0:8000
```

## Validacao rapida

Depois de subir o sistema:

- acesse `http://127.0.0.1:8000`
- faca login com um usuario valido
- confira dashboard, vendas, financeiro, lotes e relatorios

## Estrutura principal

```text
Sismgc2/
|-- abate/
|-- alimentacao/
|-- aves/
|-- calendario/
|-- core/
|-- dashboard/
|-- estoque/
|-- financeiro/
|-- genetica/
|-- historico/
|-- incubacao/
|-- linhagens/
|-- lotes/
|-- nascimentos/
|-- relatorios/
|-- sanidade/
|-- sismgc/
|-- static/
|-- templates/
|-- usuarios/
|-- vendas/
|-- manage.py
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- README.md
```

## Banco de dados

- O projeto usa SQLite por padrao.
- O arquivo `db.sqlite3` nao deve ser enviado ao GitHub.
- As migrations devem ser versionadas normalmente.
- Em outro computador, basta rodar `python manage.py migrate`.

## Static e media

- `static/` faz parte do projeto e pode ser versionado.
- `staticfiles/` nao deve ser enviado ao GitHub.
- `media/` nao deve ser enviado ao GitHub.

## Observacoes importantes

- O sistema esta preparado para uso local e em rede local.
- Para producao futura, ajuste `DEBUG=False`, `ALLOWED_HOSTS` e `SECRET_KEY` no `.env`.
- A exportacao PDF usa fallback com ReportLab quando o WeasyPrint nao consegue carregar dependencias nativas do sistema operacional.
- O projeto foi preparado para versionamento seguro, sem incluir banco local, media ou secrets.

## Versionamento

Fluxo basico para continuar versionando:

```bash
git status
git add .
git commit -m "Sua mensagem"
git push
```

# SISMGC

Sistema Inteligente de Gestao de Granja e Controle Avicola, desenvolvido com Django, Django Templates e Bootstrap 5.

## Tecnologias

- Python 3.13
- Django 6
- Django REST Framework
- SQLite
- Bootstrap 5
- OpenPyXL
- Pillow
- ReportLab
- WeasyPrint

## Modulos principais

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

## Como rodar localmente

### 1. Clonar o projeto

```bash
git clone <URL_DO_REPOSITORIO>
cd MGC-GR
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

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Criar o arquivo .env

Crie um arquivo `.env` na raiz do projeto com base no `.env.example`.

Exemplo:

```env
SECRET_KEY=sua-chave-aqui
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0
```

### 5. Rodar migrations

```bash
python manage.py migrate
```

### 6. Iniciar o servidor

```bash
python manage.py runserver
```

Para uso em rede local:

```bash
python manage.py runserver 0.0.0.0:8000
```

## Estrutura basica

```text
MGC-GR/
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
```

## Banco de dados

- O projeto usa SQLite por padrao.
- O arquivo `db.sqlite3` nao deve ser enviado ao GitHub.
- As migrations devem ser versionadas normalmente.
- Em outro computador, basta rodar `python manage.py migrate`.

## Static e media

- `static/` faz parte do projeto e pode ser versionado.
- `staticfiles/` nao deve ser enviado.
- `media/` nao deve ser enviado ao GitHub.

## Observacoes

- O projeto esta preparado para uso local e rede local.
- Para producao futura, ajuste `DEBUG=False`, `ALLOWED_HOSTS` e a `SECRET_KEY` no `.env`.
- O PDF tem fallback via ReportLab caso o WeasyPrint nao tenha dependencias nativas do sistema.

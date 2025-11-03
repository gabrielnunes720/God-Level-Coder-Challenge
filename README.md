# Maria BI - API de Analytics para Restaurantes
_Projeto desenvolvido para o "God Level Coder Challenge"_

Esta é a API backend da plataforma "Maria BI", uma solução de *analytics* flexível projetada para donos de restaurantes que não são técnicos.

Em vez de dashboards fixos, esta API fornece um "motor" de *analytics* poderoso. Ela expõe um único endpoint (`POST /api/v1/query`) que aceita "perguntas" em formato JSON e as traduz em queries SQL seguras e otimizadas contra o banco de dados PostgreSQL do desafio.

---

## 🚀 Arquitetura e Decisões Técnicas

* **Framework:** **FastAPI (Python)**
    * **Por quê?** Performance nativa, validação de dados moderna com Pydantic (que usamos no `schemas.py`) e geração automática de documentação interativa (`/docs`), o que é perfeito para testar o "contrato" da API.

* **Construtor de Query:** **SQLAlchemy (Core)**
    * **Por quê?** Esta é a decisão de segurança e flexibilidade mais importante. Em vez de concatenar strings de SQL (o que causa vulnerabilidades de **SQL Injection**), usamos o SQLAlchemy Core para construir as queries programaticamente. Nosso `query_builder.py` mapeia o JSON de "pergunta" da Maria diretamente para objetos SQLAlchemy, garantindo que apenas queries seguras sejam executadas.

* **Banco de Dados:** **PostgreSQL** (conforme requisito)
    * **Driver:** `psycopg2-binary` com *pooling* de conexão para performance.

* **"Contrato" da API:** O `schemas.py` usa `Enum` e `Pydantic` para validar rigorosamente todas as métricas, dimensões e filtros permitidos, rejeitando qualquer pedido mal formado na borda da API.

---

## 🛠️ Como Executar o Backend (Localmente)

Siga estes passos para rodar o servidor da API na sua máquina.

### Pré-requisitos

1.  **Python 3.10+** instalado.
2.  **PostgreSQL** instalado e rodando.
3.  Um banco de dados criado (ex: `restaurantes_db`).
4.  O banco de dados populado usando o script `generate_data.py` fornecido pelo desafio.

### 1. Clonar o Repositório

```bash
git clone [https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git](https://github.com/gabrielnunes720/God-Level-Coder-Challenge.git)
cd SEU_REPOSITORIO/backend
```

### 2. Criar um Ambiente Virtual

É uma boa prática isolar as dependências do projeto.

```bash
# Crie o ambiente (pasta 'venv')
python -m venv venv

# Ative o ambiente
# No macOS / Linux:
source venv/bin/activate
# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

### 3. Instalar as Dependências

Usando o arquivo que criamos:

```bash
pip install -r requirements.txt
```

### 4. Configurar o Banco de Dados

Abra o arquivo `backend/app/main.py` e edite o dicionário `DB_CONFIG` com as suas credenciais reais do PostgreSQL:

```python
# Em backend/app/main.py
DB_CONFIG = {
    "dbname": "postgres",      # O nome do seu banco
    "user": "postgres",              # Seu usuário do Postgres
    "password": "sua_senha_segura",  # Sua senha
    "host": "localhost",
    "port": "5432"
}
```

### 5. Rodar o Servidor da API

Dentro da pasta `backend`, execute o Uvicorn:

```bash
# Sintaxe: uvicorn [pasta].[arquivo]:[objeto_app] --reload
uvicorn app.main:app --reload
```
* `app.main`: Refere-se ao arquivo `backend/app/main.py`
* `app`: Refere-se ao objeto `app = FastAPI()` dentro daquele arquivo.
* `--reload`: Reinicia o servidor automaticamente quando você salvar uma alteração no código.

Se tudo deu certo, você verá uma saída parecida com:
`INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`

---

## 🧪 Como Usar (Testando a API)

A melhor parte do FastAPI: a documentação é o seu "playground" de testes.

1.  Com o servidor rodando, abra seu navegador e acesse:
    **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

2.  Você verá a documentação interativa. Clique no endpoint `POST /api/v1/query` e depois no botão "Try it out".

3.  No campo "Request body", cole o JSON abaixo para fazer uma "pergunta" de teste.

### Exemplo de Pergunta: "Top 3 Lojas por Faturamento"

```json
{
  "metrica": "faturamento_total",
  "dimensoes": [
    "loja_nome"
  ],
  "filtros": [
    {
      "campo": "status_venda",
      "operador": "eq",
      "valor": "COMPLETED"
    }
  ],
  "ordenar_por": "metrica",
  "ordem": "DESC",
  "limite": 3
}
```

4.  Clique em **"Execute"**.

A API irá usar o `query_builder` para traduzir esse JSON, executar no banco, e retornar o ranking das suas 3 melhores lojas!
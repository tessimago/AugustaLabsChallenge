# RAG Application - Augusta Labs Challenge

Sistema de Retrieval Augmented Generation (RAG) containerizado com PostgreSQL e pgvector.

## 📋 Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado e em execução
- Nada mais! Tudo está containerizado.

## 🚀 Instalação e Execução

### Opção 1: Usar imagens pré-construídas (Recomendado)

Esta é a forma mais simples - as imagens já estão no Docker Hub com a base de dados incluída.

1. Clone o repositório:
```bash
git clone https://github.com/tessimago/AugustaLabsChallenge.git
cd AugustaLabsChallenge
```

2. Execute o sistema:
```bash
docker-compose up
```

3. Aguarde a mensagem: `database system is ready to accept connections`

4. Aceda à API:
   - API: http://localhost:8000
   - Documentação interativa: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### Opção 2: Build local (Para desenvolvimento)

Se quiser modificar o código:

1. Clone o repositório
2. Certifique-se que tem o ambiente virtual configurado:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. Build e execute:
```bash
docker-compose -f docker-compose.dev.yml up --build
```

## 📡 Endpoints da API

### POST /chat
Enviar uma mensagem e receber resposta completa.

**Request:**
```json
{
  "prompt": "O que é machine learning?",
  "session_id": "user123"
}
```

**Response:**
```json
{
  "response": "Machine learning é...",
  "session_id": "user123"
}
```

### POST /chat/stream
Receber resposta em streaming (tempo real).

**Request:**
```json
{
  "prompt": "Explica-me RAG",
  "session_id": "user123"
}
```

**Response:** Stream de eventos SSE

### DELETE /session/{session_id}
Limpar histórico de conversação.

### GET /health
Verificar estado da API.

## 💻 Exemplos de Uso

### cURL
```bash
# Enviar mensagem
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!", "session_id": "test"}'

# Health check
curl http://localhost:8000/health
```

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "prompt": "O que é RAG?",
        "session_id": "minha_sessao"
    }
)

print(response.json()["response"])
```

### Python com Streaming
```python
import requests
import json

url = "http://localhost:8000/chat/stream"
payload = {"prompt": "Explica machine learning", "session_id": "demo"}

response = requests.post(url, json=payload, stream=True)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = json.loads(line[6:])
            if 'text' in data:
                print(data['text'], end="", flush=True)
```

## 🛑 Parar o Sistema
```bash
# Parar containers (mantém dados)
docker-compose down

# Parar e remover volumes (apaga dados)
docker-compose down -v
```

## 🔧 Estrutura do Projeto
```
.
├── api.py                    # Lógica da API principal
├── api_server.py             # Servidor FastAPI
├── tool_calling.py           # Sistema de tool calling
├── main.py                   # Interface CLI (legacy)
├── Dockerfile                # Build da aplicação
├── docker-compose.yml        # Orquestração (produção)
├── docker-compose.dev.yml    # Orquestração (desenvolvimento)
├── requirements.txt          # Dependências Python
└── README.md                 # Este ficheiro
```

## 🗄️ Base de Dados

A base de dados PostgreSQL com extensão pgvector está incluída na imagem Docker (`iagopaulo/rag-postgres`). 

**Nota:** A base de dados tem ~2.3GB e contém embeddings pré-calculados. O primeiro pull pode demorar alguns minutos dependendo da conexão.

### Aceder à base de dados diretamente
```bash
# Via docker exec
docker exec -it rag_postgres psql -U postgres -d augusta_labs_db

# Via pgAdmin ou outro cliente
# Host: localhost
# Port: 5432
# User: postgres
# Password: 123
# Database: augusta_labs_db
```

## 🐛 Troubleshooting

### Porta 5432 já está em uso
Se tiver PostgreSQL local a correr:
1. Pare o PostgreSQL local, OU
2. Altere a porta no `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Usar 5433 em vez de 5432
```

### Porta 8000 já está em uso
Altere a porta da aplicação:
```yaml
ports:
  - "8080:8000"  # Usar 8080 em vez de 8000
```

### Containers não iniciam
```bash
# Ver logs
docker-compose logs

# Ver logs de um serviço específico
docker-compose logs app
docker-compose logs postgres
```

### Rebuild completo
```bash
docker-compose down -v
docker-compose up --build
```

## 📦 Imagens Docker

- **App:** `iagopaulo/rag-app:latest` (~1.5GB)
- **PostgreSQL:** `iagopaulo/rag-postgres:latest` (~2.3GB)

Ambas públicas no Docker Hub.

## 🔐 Notas de Segurança

⚠️ **Este é um projeto de demonstração.** Em produção:
- Altere as credenciais da base de dados
- Use variáveis de ambiente para secrets
- Configure HTTPS
- Implemente autenticação adequada

## 📝 Requisitos do Sistema

- **RAM:** Mínimo 4GB (recomendado 8GB)
- **Disco:** ~5GB livres para imagens Docker
- **SO:** Windows 10/11, macOS, ou Linux

## 🤝 Contribuir

Este é um projeto de challenge. Para questões ou sugestões, abra uma issue.

## 📄 Licença

[Adicionar licença apropriada]

---

**Desenvolvido por:** Iago Paulo  
**Para:** Augusta Labs Challenge  
**Ano:** 2025
```

---

## Ficheiros adicionais que deves criar:

### `.gitignore`
```
# Python
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/

# Database
db_backup.sql
db_backup.dump
*.dump

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
docker-compose.override.yml

# Environment
.env
.env.local
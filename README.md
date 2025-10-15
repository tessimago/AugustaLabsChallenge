# RAG Application - Augusta Labs Challenge

## Pré-requisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado e em execução

## Instalação
```bash
# 1. Clone o repositório
git clone https://github.com/tessimago/AugustaLabsChallenge.git
cd AugustaLabsChallenge

# 2. Execute
docker-compose up

# 3. Aguarde a mensagem: "database system is ready to accept connections"
```

## Uso
**Rode o script Python:**
```python testing.py```

**Ou via cURL:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A tua pergunta aqui", "session_id": "test"}'
```

## Parar
```bash
docker-compose down
```
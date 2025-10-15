from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from api import API
from tool_calling import analyze_response
import json
import asyncio

ASSISTANT_SYSTEM_PROMPT = """
Tu és um assistente virtual português chamado IA-go.
Tu tens acesso a uma base de dados de empresas e suas informações, assim como de incentivos governamentais que podem ser dados a certas empresas se cumprirem certos requesitos.
O teu trabalho é ajudar o utilizador com qualquer dúvida relacionada a:
    - obter informação sobre os incentivos,
    - consultar dados sobre empresas,
    - explorar as correspondências entre incentivos e empresas.

Se o utilizador pedir alguma destas informações, irás fazer uma sequencia de chamadas (pode ser uma ou várias) utilizando um formato json especifico.
Eis um exemplo de como pode ser o final da tua resposta:
```json
{{
    "function": "get_incentive_by_id",
    "parameter": "<id>"
}}
```
O json, se necessario, tem que ser a ultima coisa que dizes, primeiro dá sempre uma pequena resposta re-afirmando o utilizador que irás executar o seu pedido. Depois do Json não vais dizer mais nada, e apenas esperas pela resposta para continuares e dares a informação relevante.

Todas
As funçoes possiveis que podes usar são:
- get_incentive_by_id(<id_incentive>)           # Returns a string of information about a certain incentive
- get_incentive_by_title(<title>)               # Returns the 3 most probable incentives in the database given that title/name
- get_company_by_title(<title>)                 # Returns the 3 most probable companies in the database given that title/name
- get_companies_by_incentive(<id_incentive>)    # Returns the 5 most probable companies that benefit from that incentive
Só podes chamar uma função de cada vez.
Se uma função for chamada para dar informação, dá uma resposta simples e pequena a menos que seja pedido uma descrição detalhada.
""".strip()

app = FastAPI(title="RAG API", version="1.0.0")

# Store conversation sessions, probably in production would use Redis (which i only used once in my life) or another db
sessions = {}

class PromptRequest(BaseModel):
    prompt: str
    session_id: str = "default"

class ConversationResponse(BaseModel):
    response: str
    session_id: str

@app.post("/chat", response_model=ConversationResponse)
async def chat(request: PromptRequest):
    """
    Send a prompt and get a response from the RAG system
    """
    try:
        # Get or create session
        if request.session_id not in sessions:
            api = API()
            messages = []
            api.add_system_prompt(ASSISTANT_SYSTEM_PROMPT, messages)
            sessions[request.session_id] = {
                "api": api,
                "messages": messages
            }
        
        session = sessions[request.session_id]
        api: API = session["api"]
        messages = session["messages"]
        
        # Add user prompt
        api.add_user_prompt(request.prompt, messages)
        
        # Get response
        response = api.converse(messages)
        full_response = ""
        
        for part in analyze_response(response, messages, api):
            full_response += part
        
        # Add assistant response to history
        api.add_assistant_prompt(full_response, messages)
        api.check_limit(messages, 10)
        
        return ConversationResponse(
            response=full_response.strip(),
            session_id=request.session_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: PromptRequest):
    """
    Streaming version - sends response as it's generated
    """
    async def generate():
        try:
            if request.session_id not in sessions:
                api = API()
                messages = []
                api.add_system_prompt(ASSISTANT_SYSTEM_PROMPT, messages)
                sessions[request.session_id] = {
                    "api": api,
                    "messages": messages
                }
            
            session = sessions[request.session_id]
            api: API = session["api"]
            messages = session["messages"]
            
            api.add_user_prompt(request.prompt, messages)
            
            # Run in executor to not block
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, api.converse, messages)
            
            full_response = ""
            
            # Stream each chunk immediately
            for part in analyze_response(response, messages, api):
                full_response += part
                
                # Send the chunk
                chunk_data = json.dumps({'text': part}) + '\n'
                yield f"data: {chunk_data}\n"
                
                # Small delay to ensure chunks are sent separately
                await asyncio.sleep(0.01)
            
            # Signal completion
            yield f"data: {json.dumps({'done': True})}\n\n"
            
            api.add_assistant_prompt(full_response, messages)
            api.check_limit(messages, 10)
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering if behind proxy
        }
    )


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear a conversation session
    """
    if session_id in sessions:
        del sessions[session_id]
        return {"message": f"Session {session_id} cleared"}
    return {"message": "Session not found"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {
        "message": "RAG API is running",
        "endpoints": {
            "POST /chat": "Send a prompt and get response",
            "POST /chat/stream": "Stream responses",
            "DELETE /session/{id}": "Clear conversation history",
            "GET /health": "Health check"
        }
    }
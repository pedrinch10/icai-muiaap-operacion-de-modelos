from fastapi import APIRouter, Depends

from app.schemas.chat import ChatEntrada, ChatSalida
from app.services.llm import get_llm
from app.services.orquestador import responder

router = APIRouter()


@router.post("/chat", response_model=ChatSalida)
def chat(entrada: ChatEntrada, llm=Depends(get_llm)):
    # El LLM llega por Depends para que los tests lo sustituyan por uno falso
    return responder(entrada.mensajes, llm)

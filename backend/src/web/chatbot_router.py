"""
Thin Web Layer: Chatbot Router
Điều phối HTTP Requests cho Trợ lý ảo AI Bookie (RAG Chatbot).
"""
from fastapi import APIRouter, Depends, HTTPException, status

from ..presentation.controller.ChatbotController import ChatbotController
from ..presentation.dependencies import get_chatbot_service
from ..application.services.chatbot_service import ChatbotService
from .schemas import ChatMessageWebRequest
from .serializers import serialize_chatbot_result

router = APIRouter(prefix="/chatbot", tags=["AI Chatbot Bookie"])


@router.post("/message")
def chat_with_bookie(
    request: ChatMessageWebRequest,
    chatbot_service: ChatbotService = Depends(get_chatbot_service),
):
    controller = ChatbotController(chatbot_service)
    try:
        result = controller.chat_with_bookie(request.message)
        return serialize_chatbot_result(result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Dịch vụ AI Chatbot hiện không khả dụng: {exc}",
        )

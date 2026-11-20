"""
Presentation Tier: ChatbotController
Bộ điều khiển hội thoại Trợ lý ảo AI Bookie (RAG Chatbot) (Pure OOP).
Sinh mã từ Visual Paradigm: Không phụ thuộc Framework Web (FastAPI), không dùng DTO.
"""
from ...application.services.chatbot_service import ChatbotService
from ...application.services.chatbot_result import ChatbotResult


class ChatbotController:
    """Bộ điều khiển quy trình tư vấn và hội thoại AI."""

    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot_service = chatbot_service

    def chat_with_bookie(self, message: str) -> ChatbotResult:
        if not message or not message.strip():
            raise ValueError("Tin nhắn không được để trống.")
        return self.chatbot_service.process_message(message.strip())

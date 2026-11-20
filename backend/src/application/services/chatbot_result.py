"""
Application Tier Runtime Class: ChatbotResult
Đóng gói kết quả phản hồi của Trợ lý ảo AI Bookie (RAG Chatbot).
Tương tự lớp SearchResult trong thiết kế UML chuẩn của Visual Paradigm.
"""
from typing import List, Dict, Any


class ChatbotResult:
    """Lớp runtime mang dữ liệu phản hồi hội thoại và thẻ gợi ý sách."""

    def __init__(self, reply: str, suggested_books: List[Dict[str, Any]]):
        self.reply = reply
        self.suggested_books = suggested_books

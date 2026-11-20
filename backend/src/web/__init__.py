"""
Thin Web Layer: Package entrypoint
"""
from .admin_router import router as admin_router
from .auth_router import router as auth_router
from .book_router import router as book_router
from .cart_router import router as cart_router
from .chatbot_router import router as chatbot_router
from .checkout_router import router as checkout_router
from .payment_router import router as payment_router
from .search_router import router as search_router

__all__ = [
    "admin_router",
    "auth_router",
    "book_router",
    "cart_router",
    "chatbot_router",
    "checkout_router",
    "payment_router",
    "search_router",
]

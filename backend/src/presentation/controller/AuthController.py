"""
Presentation Tier: AuthController
Bộ điều khiển xác thực tài khoản và hồ sơ người dùng (Pure OOP).
Sinh mã từ Visual Paradigm: Không phụ thuộc Framework Web (FastAPI), không dùng DTO.
"""
from typing import Optional, List, Tuple
from ...domain.entities.user import User
from ...domain.entities.order import Order
from ...application.services.auth_service import AuthService
from ...infrastructure.repositories.order_repository import OrderRepository


class AuthController:
    """Bộ điều khiển quản lý phiên đăng nhập và định danh tài khoản."""

    def __init__(
        self,
        auth_service: AuthService,
        order_repo: OrderRepository,
    ):
        self.auth_service = auth_service
        self.order_repo = order_repo

    def login(self, username: str, password: str) -> Tuple[str, User]:
        return self.auth_service.login(username=username, password=password)

    def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str] = None,
        shipping_address: Optional[str] = None,
    ) -> Tuple[str, User]:
        return self.auth_service.register(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            phone=phone,
            shipping_address=shipping_address,
        )

    def get_profile(self, user_id: str) -> User:
        return self.auth_service.get_profile(user_id)

    def get_user_orders(self, user_id: str) -> List[Order]:
        return self.order_repo.get_orders_by_customer(user_id)

"""
Presentation Tier: CartController
Bộ điều khiển nghiệp vụ giỏ hàng (Pure OOP).
Sinh mã từ Visual Paradigm: Không phụ thuộc Framework Web (FastAPI), không dùng DTO.
"""
from typing import Optional
from ...domain.entities.cart import Cart
from ...application.services.cart_service import CartService


class CartController:
    """Bộ điều khiển quy trình quản lý giỏ hàng của độc giả."""

    def __init__(self, cart_service: CartService):
        self.cart_service = cart_service

    def get_cart(self, customer_id: int) -> Cart:
        return self.cart_service.get_cart(int(customer_id))

    def add_to_cart(self, customer_id: int, product_id: int, quantity: int = 1) -> Cart:
        return self.cart_service.add_to_cart(
            customer_id=int(customer_id),
            product_id=int(product_id),
            quantity=int(quantity),
        )

    def update_item_quantity(self, customer_id: int, product_id: int, quantity: int) -> Cart:
        return self.cart_service.update_quantity(
            customer_id=int(customer_id),
            product_id=int(product_id),
            quantity=int(quantity),
        )

    def remove_item(self, customer_id: int, product_id: int) -> Cart:
        return self.cart_service.remove_item(
            customer_id=int(customer_id),
            product_id=int(product_id),
        )

    def clear_cart(self, customer_id: int) -> Cart:
        return self.cart_service.clear_cart(int(customer_id))

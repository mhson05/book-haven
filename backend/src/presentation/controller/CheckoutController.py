"""
Presentation Tier: CheckoutController
Bộ điều khiển quy trình đặt hàng và giao vận 10 bước (Pure OOP).
Sinh mã từ Visual Paradigm: Không phụ thuộc Framework Web (FastAPI), không dùng DTO.
"""
from typing import Optional, Dict, Any
from ...domain.entities.order import Order
from ...application.services.checkout_service import CheckoutService


class CheckoutController:
    """Bộ điều khiển quy trình đặt hàng và giao vận."""

    def __init__(self, checkout_service: CheckoutService):
        self.checkout_service = checkout_service

    def execute_checkout(
        self,
        customer_id: int,
        cart_id: int,
        receiver_name: str,
        receiver_phone: str,
        shipping_address: str,
        payment_method: str = "VIETQR",
        carrier: str = "GHN_STANDARD",
        voucher_code: Optional[str] = None,
    ) -> Order:
        return self.checkout_service.checkout(
            customer_id=int(customer_id),
            cart_id=int(cart_id),
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            shipping_address=shipping_address,
            payment_method=payment_method,
            carrier=carrier,
            voucher_code=voucher_code,
        )

    def get_shipping_options(self, cart_id: Optional[str] = None) -> Dict[str, Any]:
        return self.checkout_service.get_shipping_options(cart_id)

"""
Presentation Tier: PaymentController
Bộ điều khiển xác nhận thanh toán VietQR và đối soát Webhook (Pure OOP).
Sinh mã từ Visual Paradigm: Không phụ thuộc Framework Web (FastAPI), không dùng DTO.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from ...domain.entities.order import Order
from ...application.services.payment_service import PaymentService
from ...application.services.inventory_service import InventoryService


class PaymentController:
    """Bộ điều khiển thanh toán và theo dõi vận đơn."""

    def __init__(
        self,
        payment_service: PaymentService,
        inventory_service: Optional[InventoryService] = None,
    ):
        self.payment_service = payment_service
        self.inventory_service = inventory_service

    def confirm_payment(
        self, order_id: int, transaction_code: Optional[str] = None
    ) -> Order:
        return self.payment_service.confirm_payment(
            order_id=int(order_id),
            transaction_code=transaction_code,
        )

    def receive_bank_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.payment_service.process_webhook(payload)

    def get_order_payment_status(self, order_id: str) -> Dict[str, Any]:
        order_status = self.payment_service.get_order_status(int(order_id))
        if (
            self.inventory_service is not None
            and order_status.get("status") == "SHIPPING"
            and order_status.get("carrier") == "HANOI_DRONE"
            and order_status.get("updated_at")
        ):
            try:
                raw_time = str(order_status["updated_at"]).split(".")[0]
                updated_dt = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
                if (datetime.now() - updated_dt).total_seconds() >= 25:
                    self.inventory_service.mark_delivered(int(order_id))
                    order_status = self.payment_service.get_order_status(int(order_id))
            except Exception:
                pass
        return order_status

    def mark_order_delivered(self, order_id: str) -> Order:
        if self.inventory_service is None:
            raise ValueError("Thiếu InventoryService.")
        return self.inventory_service.mark_delivered(int(order_id))

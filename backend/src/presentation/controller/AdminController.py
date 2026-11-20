"""
Presentation Tier: AdminController
Bộ điều khiển quản trị kho, bàn giao bưu kiện và báo cáo doanh thu (Pure OOP).
Sinh mã từ Visual Paradigm: Không phụ thuộc Framework Web (FastAPI), không dùng DTO.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from ...domain.entities.order import Order
from ...domain.entities.product import Product
from ...application.services.inventory_service import InventoryService
from ...infrastructure.repositories.order_repository import OrderRepository


class AdminController:
    """Bộ điều khiển quản trị back-office dành cho Admin và Thủ kho."""

    def __init__(
        self,
        inventory_service: InventoryService,
        order_repo: OrderRepository,
    ):
        self.inventory_service = inventory_service
        self.order_repo = order_repo

    def get_inventory(self) -> List[Dict[str, Any]]:
        return self.inventory_service.get_inventory_status()

    def restock(self, product_id: int, quantity: int) -> Product:
        return self.inventory_service.restock(int(product_id), int(quantity))

    def get_orders(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        orders = self.order_repo.get_all_orders(limit=limit, offset=offset)
        for ord_dict in orders:
            if (
                ord_dict.get("status") == "SHIPPING"
                and ord_dict.get("carrier") == "HANOI_DRONE"
                and ord_dict.get("updated_at")
            ):
                try:
                    raw_time = str(ord_dict["updated_at"]).split(".")[0]
                    updated_dt = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
                    if (datetime.now() - updated_dt).total_seconds() >= 25:
                        self.inventory_service.mark_delivered(int(ord_dict["order_id"]))
                        ord_dict["status"] = "DELIVERED"
                except Exception:
                    pass
        return orders

    def dispatch_order(
        self, order_id: int, carrier_name: Optional[str] = None
    ) -> Order:
        return self.inventory_service.dispatch_order(
            int(order_id), carrier_name=carrier_name
        )

    def get_revenue_report(self) -> Dict[str, Any]:
        return self.inventory_service.get_revenue_report()

"""
Application Service: InventoryService
Điều phối nhập kho (Restock), xử lý tự động giải phóng giữ chỗ quá hạn 15 phút (Background Worker),
và nghiệp vụ xuất kho/bàn giao giao vận Drone/GHN của Quản trị viên & Thủ kho.
Tuân thủ chuẩn UML Visual Paradigm: Nhận tham số nguyên thủy, trả về trực tiếp Domain Entity Product và Order.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from ...domain.entities.order import Order
from ...domain.entities.stock_reservation import StockReservation
from ...domain.entities.product import Product
from ...domain.exceptions import (
    EntityNotFoundException,
    InvalidOrderStateException,
    DroneOverweightException,
)
from ...infrastructure.database import DatabaseSession
from ...infrastructure.repositories.book_repository import BookRepository
from ...infrastructure.repositories.order_repository import OrderRepository


class InventoryService:
    def __init__(
        self,
        session: DatabaseSession,
        book_repo: BookRepository,
        order_repo: OrderRepository,
    ):
        self.session = session
        self.book_repo = book_repo
        self.order_repo = order_repo

    def restock(self, product_id: int, quantity: int) -> Product:
        """Thủ kho nhập thêm sản phẩm vào kho (UC12)."""
        if quantity <= 0:
            raise ValueError("Số lượng nhập kho phải lớn hơn 0.")

        self.session.begin_transaction()
        try:
            product = self.book_repo.get_product_by_id(product_id)
            if not product:
                raise EntityNotFoundException("Product", str(product_id))

            product.restock(quantity)
            self.book_repo.update_product_stock(product)
            self.session.commit()
            return product
        except Exception as e:
            self.session.rollback()
            raise e

    def cleanup_expired_reservations(
        self, current_time: Optional[datetime] = None
    ) -> int:
        """
        Background Worker định kỳ quét và giải phóng các bản ghi giữ chỗ quá hạn 15 phút (BR03).
        Hoàn trả lại tồn kho khả dụng cho khách hàng khác và hủy đơn hàng chưa thanh toán.
        """
        expired_list = self.order_repo.get_pending_expired_reservations()
        if not expired_list:
            return 0

        self.session.begin_transaction()
        try:
            released_count = 0
            affected_order_ids = set()

            for res in expired_list:
                prod = self.book_repo.get_product_by_id(res["product_id"])
                if prod:
                    prod.release_stock(res["reserved_quantity"])
                    self.book_repo.update_product_stock(prod)

                self.order_repo.update_reservation_status(
                    res["reservation_id"], "RELEASED"
                )
                affected_order_ids.add(res["order_id"])
                released_count += 1

            for oid in affected_order_ids:
                order = self.order_repo.get_order_by_id(oid)
                if order and order.status in ("AWAITING_PAYMENT", "PENDING_PAYMENT"):
                    order.cancel("Hết hạn thanh toán 15 phút")
                    self.order_repo.save_order(order)

            self.session.commit()
            return released_count

        except Exception as e:
            self.session.rollback()
            raise e

    def dispatch_order(
        self, order_id: int, carrier_name: Optional[str] = None
    ) -> Order:
        """
        Thủ kho đóng gói và bàn giao bưu kiện cho Đối tác vận chuyển (Hanoi Drone hoặc GHN).
        Khởi tạo mã vận đơn (tracking_code), chuyển trạng thái sang SHIPPING và trả về đối tượng Order.
        """
        self.session.begin_transaction()
        try:
            order = self.order_repo.get_order_by_id(order_id)
            if not order:
                raise EntityNotFoundException("Order", str(order_id))

            if order.status == "PAID":
                order.transition_to("PACKED")
            elif order.status in ("PENDING_CASH", "AWAITING_PAYMENT") and order.payment_method == "COD":
                order.transition_to("PACKED")
            elif order.status != "PACKED":
                raise InvalidOrderStateException(
                    f"Đơn hàng đang ở trạng thái '{order.status}', chưa thể giao vận."
                )

            carrier = carrier_name if carrier_name else (order.carrier or "GHN")

            if "DRONE" in carrier.upper():
                total_pkg_weight = order.calculate_total_weight() + 150
                if total_pkg_weight > 2000:
                    raise DroneOverweightException(
                        total_weight_grams=total_pkg_weight, max_allowed=2000
                    )
                tracking_code = f"DRONE-HN-{uuid.uuid4().hex[:6].upper()}"
            elif "EXP" in carrier.upper():
                tracking_code = f"GHN-EXP-{uuid.uuid4().hex[:8].upper()}"
            else:
                tracking_code = f"GHN-STD-{uuid.uuid4().hex[:8].upper()}"

            order.transition_to("SHIPPING")
            order._carrier = carrier
            order._tracking_code = tracking_code
            self.order_repo.save_order(order)
            self.session.commit()
            return order

        except Exception as e:
            self.session.rollback()
            raise e

    def mark_delivered(self, order_id: int) -> Order:
        """Cập nhật đơn hàng đã giao thành công và trả về đối tượng Order."""
        self.session.begin_transaction()
        try:
            order = self.order_repo.get_order_by_id(order_id)
            if not order:
                raise EntityNotFoundException("Order", str(order_id))

            if order.status in ("PAID", "PENDING_CASH"):
                carrier = order.carrier or "HANOI_DRONE"
                tracking = order.tracking_code or f"DRONE-HN-{uuid.uuid4().hex[:6].upper()}"
                order.transition_to("PACKED")
                order.transition_to("SHIPPING")
                order._carrier = carrier
                order._tracking_code = tracking
            elif order.status == "PACKED":
                order.transition_to("SHIPPING")

            order.transition_to("DELIVERED")
            self.order_repo.save_order(order)

            if order.payment_method == "COD":
                for item in order.items:
                    prod = self.book_repo.get_product_by_id(item.product_id)
                    if prod:
                        prod.commit_stock(item.quantity)
                        self.book_repo.update_product_stock(prod)
                self.order_repo.update_reservations_status_by_order(
                    order_id, "COMMITTED"
                )
                from ...domain.entities.payment import Payment

                payment = Payment(
                    order_id=order_id,
                    payment_method="COD",
                    amount=order.final_amount,
                    transaction_code=f"COD_{order_id}_{int(datetime.now().timestamp())}",
                    status="SUCCESS",
                    paid_at=datetime.utcnow(),
                )
                self.order_repo.save_payment_record(payment)

            self.session.commit()
            return order
        except Exception as e:
            self.session.rollback()
            raise e

    def get_inventory_status(self) -> List[Dict[str, Any]]:
        """Lấy danh sách tất cả sản phẩm và trạng thái tồn kho thực tế / giữ chỗ / khả dụng."""
        return self.book_repo.get_inventory_status()

    def get_revenue_report(self) -> Dict[str, Any]:
        """Báo cáo doanh thu thực thu và top bán chạy (BR06)."""
        return self.order_repo.get_revenue_summary()

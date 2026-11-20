"""
Application Service: CheckoutService
Điều phối quy trình Đặt hàng và Checkout 10 bước bọc trong ranh giới Transaction CSDL.
Tuân thủ chuẩn UML Visual Paradigm: Nhận tham số nguyên thủy, trả về trực tiếp Domain Entity Order.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from ...domain.entities.order import Order
from ...domain.entities.order_item import OrderItem
from ...domain.entities.stock_reservation import StockReservation
from ...domain.exceptions import OutOfStockException, DroneOverweightException
from ...infrastructure.database import DatabaseSession
from ...infrastructure.repositories.book_repository import BookRepository
from ...infrastructure.repositories.cart_repository import CartRepository
from ...infrastructure.repositories.order_repository import OrderRepository
from ...infrastructure.adapters.vietqr_service import VietQRService


class CheckoutService:
    def __init__(
        self,
        session: DatabaseSession,
        book_repo: BookRepository,
        cart_repo: CartRepository,
        order_repo: OrderRepository,
        vietqr_service: VietQRService,
        reservation_ttl_minutes: int = 15,
    ):
        self.session = session
        self.book_repo = book_repo
        self.cart_repo = cart_repo
        self.order_repo = order_repo
        self.vietqr_service = vietqr_service
        self.reservation_ttl_minutes = reservation_ttl_minutes

    def checkout(
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
        """
        Thực thi Quy trình Đặt hàng và Checkout 10 bước bọc trong ranh giới Giao dịch ACID.
        Trả về đối tượng Order của tầng miền (Domain Entity).
        """
        self.session.begin_transaction()
        try:
            # Bước 1: Nạp giỏ hàng của khách
            cart = self.cart_repo.get_cart_by_id(int(cart_id))
            if not cart or not cart.items:
                raise ValueError("Giỏ hàng đang rỗng, không thể tiến hành đặt hàng.")

            # Bước 2 & 3: Kiểm tra tồn kho khả dụng cho từng sản phẩm (BR02)
            products_map = {}
            for item in cart.items:
                pid = item.product_id
                prod = self.book_repo.get_product_by_id(pid)
                if not prod:
                    raise ValueError(f"Sản phẩm {pid} không tồn tại trong kho.")
                if not prod.check_availability(item.quantity):
                    raise OutOfStockException(
                        sku=prod.sku,
                        requested=item.quantity,
                        available=prod.get_available_stock(),
                    )
                products_map[pid] = prod

            # Bước 4: Tính tổng trọng lượng gram & Kiểm tra tải trọng Drone (BR05)
            total_pkg_weight_grams = cart.calculate_total_weight() + 150  # 150g màng xốp + hộp
            carrier_upper = str(carrier or "GHN").upper()

            # Ràng buộc Drone tải trọng tối đa 2000g
            if "DRONE" in carrier_upper and total_pkg_weight_grams > 2000:
                raise DroneOverweightException(
                    total_weight_grams=total_pkg_weight_grams, max_allowed=2000
                )

            # Ràng buộc Drone không hỗ trợ thanh toán tiền mặt COD
            if "DRONE" in carrier_upper and str(payment_method).upper() == "COD":
                raise ValueError(
                    "Giao hàng bằng Drone không hỗ trợ thanh toán tiền mặt (COD). "
                    "Vui lòng thanh toán trực tuyến qua VietQR."
                )

            # Tính cước phí giao vận
            if "DRONE" in carrier_upper:
                shipping_fee = 60000
            elif "EXP" in carrier_upper:
                shipping_fee = 45000
            else:
                shipping_fee = 25000

            subtotal_amount = cart.calculate_subtotal()

            # Giảm giá nếu có voucher
            discount_amount = 0
            if voucher_code and voucher_code.upper() in ("BOOKHAVEN10", "VOUCHER10"):
                discount_amount = min(50000, int(subtotal_amount * 0.1))
            elif voucher_code and voucher_code.upper() == "FREESHIP":
                discount_amount = shipping_fee

            final_amount = max(0, subtotal_amount + shipping_fee - discount_amount)

            initial_status = (
                "PENDING_CASH"
                if str(payment_method).upper() == "COD"
                else "AWAITING_PAYMENT"
            )

            # Bước 5: Khởi tạo Order & OrderItem
            order = Order(
                customer_id=int(customer_id),
                receiver_name=receiver_name,
                receiver_phone=receiver_phone,
                shipping_address=shipping_address,
                payment_method=str(payment_method).upper(),
                carrier=carrier_upper,
                total_amount=subtotal_amount,
                shipping_fee=shipping_fee,
                discount_amount=discount_amount,
                final_amount=final_amount,
                status=initial_status,
                items=[],
            )
            # Lưu Order trước để nhận auto-increment order_id
            assigned_order_id = self.order_repo.save_order(order)
            order._order_id = assigned_order_id

            order_items = []
            for item in cart.items:
                prod = products_map[item.product_id]
                oi = OrderItem(
                    order_id=assigned_order_id,
                    product_id=prod.product_id,
                    product_name_snapshot=prod.name,
                    sku_snapshot=prod.sku,
                    product_kind_snapshot=getattr(prod, "binding_type", "Product"),
                    unit_price_at_purchase=prod.unit_price,
                    quantity=item.quantity,
                    weight_gram_snapshot=prod.weight_gram,
                )
                order_items.append(oi)

            order._items = order_items
            self.order_repo.save_order(order)

            # Bước 6: Khóa giữ chỗ tồn kho 15 phút (Stock Reservation - BR03)
            expires_at = datetime.utcnow() + timedelta(minutes=self.reservation_ttl_minutes)
            for item in cart.items:
                prod = products_map[item.product_id]
                prod.reserve_stock(item.quantity)
                self.book_repo.update_product_stock(prod)

                res = StockReservation(
                    order_id=assigned_order_id,
                    product_id=prod.product_id,
                    reserved_quantity=item.quantity,
                    expires_at=expires_at,
                    status="PENDING",
                )
                self.order_repo.save_stock_reservation(res)

            # Bước 7: Sinh mã VietQR động nếu chọn chuyển khoản
            vietqr_data = None
            if order.payment_method == "VIETQR":
                vietqr_data = self.vietqr_service.generate_payment_qr(
                    str(assigned_order_id), order.final_amount
                )

            # Bước 8: Làm rỗng giỏ hàng
            self.cart_repo.clear_cart(int(cart_id))

            # Bước 9: Commit transaction
            self.session.commit()

            # Gắn các dữ liệu bổ sung vào object order để tầng web bóc tách
            order.vietqr_data = vietqr_data
            order.reservation_expires_at = expires_at.strftime("%Y-%m-%d %H:%M:%S")

            # Bước 10: Trả về đối tượng Domain Entity Order
            return order

        except Exception as e:
            self.session.rollback()
            raise e

    def get_shipping_options(self, cart_id: Optional[str] = None) -> Dict[str, Any]:
        """Tính toán cước phí và tính khả dụng của Drone theo trọng lượng giỏ hàng."""
        weight_grams = 0
        is_drone_eligible = True

        if cart_id and cart_id.strip():
            try:
                cart = self.cart_repo.get_cart_by_id(int(cart_id.strip()))
                if cart:
                    weight_grams = cart.calculate_total_weight() + 150
                    is_drone_eligible = cart.validate_drone_payload()
            except Exception:
                pass

        options = [
            {
                "code": "GHN_STANDARD",
                "name": "Giao Hàng Nhanh - Tiêu chuẩn (GHN)",
                "estimated_time": "2 - 3 ngày",
                "fee": 25000,
                "is_eligible": True,
                "ineligible_reason": None,
            },
            {
                "code": "GHN_EXPRESS",
                "name": "Giao Hàng Nhanh - Hỏa tốc đường bộ",
                "estimated_time": "Trong 24 giờ",
                "fee": 45000,
                "is_eligible": True,
                "ineligible_reason": None,
            },
            {
                "code": "HANOI_DRONE",
                "name": "Hanoi Drone Express (Giao hàng không người lái hỏa tốc)",
                "estimated_time": "30 - 45 phút",
                "fee": 60000,
                "is_eligible": is_drone_eligible,
                "ineligible_reason": (
                    f"Tổng khối lượng ({weight_grams}g) vượt quá tải trọng bay tối đa của Drone (2.000g)."
                    if not is_drone_eligible
                    else None
                ),
            },
        ]

        return {
            "cart_id": cart_id,
            "calculated_package_weight_grams": weight_grams,
            "drone_max_payload_grams": 2000,
            "options": options,
        }

"""
Application Service: CartService
Điều phối các nghiệp vụ giỏ hàng của độc giả: xem, thêm, sửa số lượng, xóa và làm rỗng.
Tuân thủ chuẩn UML Visual Paradigm: Nhận tham số nguyên thủy, trả về trực tiếp Domain Entity Cart.
"""
from typing import Optional
from ...domain.entities.cart import Cart
from ...domain.exceptions import EntityNotFoundException, OutOfStockException
from ...infrastructure.repositories.cart_repository import CartRepository
from ...infrastructure.repositories.book_repository import BookRepository


class CartService:
    def __init__(self, cart_repo: CartRepository, book_repo: BookRepository):
        self.cart_repo = cart_repo
        self.book_repo = book_repo

    def get_cart(self, customer_id: int) -> Cart:
        """Lấy giỏ hàng hiện tại của khách hàng (hoặc tạo mới nếu chưa có)."""
        return self.cart_repo.get_or_create_cart(int(customer_id))

    def add_to_cart(self, customer_id: int, product_id: int, quantity: int = 1) -> Cart:
        """Thêm sản phẩm vào giỏ hàng, kiểm tra tồn kho khả dụng (BR02)."""
        if quantity <= 0:
            raise ValueError("Số lượng thêm vào giỏ phải lớn hơn 0.")

        product = self.book_repo.get_product_by_id(int(product_id))
        if not product:
            raise EntityNotFoundException("Product", str(product_id))

        cart = self.cart_repo.get_or_create_cart(int(customer_id))

        # Tìm số lượng hiện có trong giỏ
        current_in_cart = 0
        for item in cart.items:
            if item.product_id == int(product_id):
                current_in_cart = item.quantity
                break

        new_total_quantity = current_in_cart + quantity

        # Kiểm tra tồn kho khả dụng (BR02)
        if not product.check_availability(new_total_quantity):
            raise OutOfStockException(
                sku=product.sku,
                requested=new_total_quantity,
                available=product.get_available_stock(),
            )

        cart.add_item(product, quantity)
        self.cart_repo.save_item(cart.cart_id, int(product_id), new_total_quantity)

        # Trả về giỏ hàng đã cập nhật
        return self.cart_repo.get_cart_by_id(cart.cart_id)

    def update_quantity(self, customer_id: int, product_id: int, quantity: int) -> Cart:
        """Cập nhật số lượng của một mục trong giỏ."""
        cart = self.cart_repo.get_or_create_cart(int(customer_id))

        found_item = None
        for item in cart.items:
            if item.product_id == int(product_id) or str(item.cart_item_id) == str(product_id):
                found_item = item
                break

        if not found_item:
            raise EntityNotFoundException("CartItem", str(product_id))

        if quantity <= 0:
            return self.remove_item(customer_id, found_item.product_id)

        product = self.book_repo.get_product_by_id(found_item.product_id)
        if not product:
            raise EntityNotFoundException("Product", str(found_item.product_id))

        if not product.check_availability(quantity):
            raise OutOfStockException(
                sku=product.sku,
                requested=quantity,
                available=product.get_available_stock(),
            )

        cart.update_item_quantity(found_item.cart_item_id, quantity)
        self.cart_repo.save_item(cart.cart_id, found_item.product_id, quantity)
        return self.cart_repo.get_cart_by_id(cart.cart_id)

    def remove_item(self, customer_id: int, product_id: int) -> Cart:
        """Xóa một sản phẩm khỏi giỏ hàng."""
        cart = self.cart_repo.get_or_create_cart(int(customer_id))
        self.cart_repo.remove_item(cart.cart_id, int(product_id))
        return self.cart_repo.get_cart_by_id(cart.cart_id)

    def clear_cart(self, customer_id: int) -> Cart:
        """Làm rỗng toàn bộ giỏ hàng."""
        cart = self.cart_repo.get_or_create_cart(int(customer_id))
        self.cart_repo.clear_cart(cart.cart_id)
        return self.cart_repo.get_cart_by_id(cart.cart_id)

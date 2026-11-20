"""
Presentation Tier: ProductCatalogController
Bộ điều khiển danh mục và chi tiết sản phẩm / sách (Pure OOP).
Sinh mã từ Visual Paradigm: Không phụ thuộc Framework Web (FastAPI), không dùng DTO.
"""
from typing import Dict, Any, List, Optional
from ...infrastructure.repositories.book_repository import BookRepository


class ProductCatalogController:
    """Bộ điều khiển danh mục và chi tiết sản phẩm / sách."""

    def __init__(self, book_repo: BookRepository):
        self.book_repo = book_repo

    def list_books(
        self,
        category_id: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        limit: int = 500,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        return self.book_repo.get_all_books(
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            limit=limit,
            offset=offset,
        )

    def get_book_detail(self, book_id: str) -> Dict[str, Any]:
        book = self.book_repo.get_book_by_id(book_id)
        if not book:
            return {}

        editions = self.book_repo.get_editions_by_book_id(int(book_id))
        editions_data = [
            {
                "edition_id": ed.product_id,
                "sku": ed.sku,
                "isbn13": getattr(ed, "isbn13", ""),
                "binding_type": getattr(ed, "binding_type", "Standard"),
                "unit_price": ed.unit_price,
                "weight_gram": ed.weight_gram,
                "stock_on_hand": ed.stock_on_hand,
                "stock_reserved": ed.stock_reserved,
                "available_stock": ed.get_available_stock(),
                "is_in_stock": ed.get_available_stock() > 0,
            }
            for ed in editions
        ]
        return {**book, "editions": editions_data}

    def list_categories(self) -> List[Dict[str, Any]]:
        return self.book_repo.get_all_categories()

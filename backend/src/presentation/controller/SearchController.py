"""
Presentation Tier: SearchController
Bộ điều khiển tìm kiếm đa phương thức (SQL, Semantic AI, dHash) (Pure OOP).
Sinh mã từ Visual Paradigm: Không phụ thuộc Framework Web (FastAPI), không dùng DTO.
"""
from typing import Optional
from ...application.services.search_service import SearchService
from ...application.services.search_result import SearchResult


class SearchController:
    """Bộ điều khiển tìm kiếm đa phương thức."""

    def __init__(self, search_service: SearchService):
        self.search_service = search_service

    def search_keyword(
        self,
        keyword: str,
        category_id: Optional[str] = None,
        binding_type: Optional[str] = None,
        limit: int = 20,
    ) -> SearchResult:
        return self.search_service.search_keyword(
            keyword=keyword,
            category_id=category_id,
            binding_type=binding_type,
            limit=limit,
        )

    def search_semantic(
        self,
        query: str,
        limit: int = 5,
    ) -> SearchResult:
        return self.search_service.search_semantic(
            query=query,
            limit=limit,
            min_threshold=0.50,
        )

    def search_by_image(
        self,
        image_bytes: bytes,
        base_static_path: Optional[str] = None,
    ) -> SearchResult:
        if not image_bytes:
            raise ValueError("Tệp ảnh trống.")
        return self.search_service.search_by_image(
            image_bytes=image_bytes,
            base_static_path=base_static_path,
        )

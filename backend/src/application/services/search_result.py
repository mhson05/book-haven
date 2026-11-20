"""
Application Tier Runtime Class: SearchResult
Đóng gói danh sách kết quả tìm kiếm đa phương thức (SQL, Semantic Vector, dHash).
Khớp 100% với lớp SearchResult của bạn NhiCT và giáo trình thầy Quế.
"""
from typing import List, Dict, Any


class SearchResult:
    """Lớp runtime chứa danh sách các sản phẩm tìm được và chế độ tìm kiếm."""

    def __init__(self, results: List[Dict[str, Any]], search_mode: str = "keyword"):
        self.results = results
        self.total_found = len(results)
        self.search_mode = search_mode

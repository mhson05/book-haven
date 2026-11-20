"""
Thin Web Layer: Book Catalog Router
Điều phối HTTP Requests cho Duyệt danh mục sách, Chi tiết sản phẩm và Thể loại.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..presentation.controller.ProductCatalogController import ProductCatalogController
from ..infrastructure.repositories.book_repository import BookRepository
from ..presentation.dependencies import get_book_repo

router = APIRouter(tags=["Books & Categories"])


@router.get("/books")
def list_books(
    category_id: Optional[str] = Query(None, description="Lọc theo mã thể loại"),
    min_price: Optional[int] = Query(None, description="Giá thấp nhất"),
    max_price: Optional[int] = Query(None, description="Giá cao nhất"),
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    book_repo: BookRepository = Depends(get_book_repo),
):
    controller = ProductCatalogController(book_repo)
    books = controller.list_books(
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
        offset=offset,
    )
    return {"total": len(books), "books": books}


@router.get("/books/{book_id}")
def get_book_detail(book_id: str, book_repo: BookRepository = Depends(get_book_repo)):
    controller = ProductCatalogController(book_repo)
    detail = controller.get_book_detail(book_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đầu sách với ID '{book_id}'.",
        )
    return detail


@router.get("/categories")
def list_categories(book_repo: BookRepository = Depends(get_book_repo)):
    controller = ProductCatalogController(book_repo)
    categories = controller.list_categories()
    return {"total": len(categories), "categories": categories}

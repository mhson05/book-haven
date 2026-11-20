"""
Thin Web Layer: Search Router
Điều phối HTTP Requests cho Tìm kiếm đa phương thức (Keyword SQL, Semantic AI, Image dHash).
"""
import os
from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException, status

from ..presentation.controller.SearchController import SearchController
from ..presentation.dependencies import get_search_service
from ..application.services.search_service import SearchService
from .schemas import SemanticSearchWebRequest
from .serializers import serialize_search_result

router = APIRouter(prefix="/search", tags=["Search Multi-Modal"])

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))


@router.get("")
@router.get("/keyword")
def search_keyword(
    q: str = Query(..., min_length=1, description="Từ khóa tìm kiếm tiêu đề, tác giả"),
    category_id: Optional[str] = Query(None, description="Mã thể loại lọc"),
    binding_type: Optional[str] = Query(None, description="Quy cách ấn bản: Paperback / Hardcover"),
    limit: int = Query(20, ge=1, le=50),
    search_service: SearchService = Depends(get_search_service),
):
    controller = SearchController(search_service)
    result = controller.search_keyword(
        keyword=q,
        category_id=category_id,
        binding_type=binding_type,
        limit=limit,
    )
    return serialize_search_result(result)


@router.post("/semantic")
def search_semantic(
    request: SemanticSearchWebRequest,
    search_service: SearchService = Depends(get_search_service),
):
    controller = SearchController(search_service)
    result = controller.search_semantic(query=request.query, limit=request.limit)
    return serialize_search_result(result)


@router.post("/image")
async def search_by_cover_image(
    file: UploadFile = File(..., description="Ảnh bìa chụp từ camera hoặc thiết bị của độc giả"),
    search_service: SearchService = Depends(get_search_service),
):
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tệp ảnh trống.")

    controller = SearchController(search_service)
    try:
        result = controller.search_by_image(image_bytes=image_bytes, base_static_path=ASSETS_DIR)
        return serialize_search_result(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xử lý nhận diện ảnh bìa: {str(e)}",
        )

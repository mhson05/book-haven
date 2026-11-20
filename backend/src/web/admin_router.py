"""
Thin Web Layer: Admin Router
Điều phối HTTP Requests cho Quản trị viên và Thủ kho (Nhập kho, Vận đơn, Doanh thu).
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..presentation.controller.AdminController import AdminController
from ..presentation.dependencies import (
    get_inventory_service,
    get_order_repo,
    require_admin,
)
from ..application.services.inventory_service import InventoryService
from ..infrastructure.repositories.order_repository import OrderRepository
from ..domain.exceptions import (
    EntityNotFoundException,
    InvalidOrderStateException,
    DroneOverweightException,
)
from .schemas import RestockWebRequest, DispatchOrderWebRequest
from .serializers import serialize_order

router = APIRouter(
    prefix="/admin",
    tags=["Admin & Back-office"],
    dependencies=[Depends(require_admin)],
)


@router.get("/inventory")
def get_inventory(
    inventory_service: InventoryService = Depends(get_inventory_service),
    order_repo: OrderRepository = Depends(get_order_repo),
):
    controller = AdminController(inventory_service, order_repo)
    return {"inventory": controller.get_inventory()}


@router.post("/inventory/restock")
def restock(
    request: RestockWebRequest,
    inventory_service: InventoryService = Depends(get_inventory_service),
    order_repo: OrderRepository = Depends(get_order_repo),
):
    controller = AdminController(inventory_service, order_repo)
    try:
        updated_edition = controller.restock(
            product_id=int(request.edition_id), quantity=request.quantity
        )
        return {
            "message": f"Nhập kho thành công +{request.quantity} cuốn cho SKU '{updated_edition.sku}'.",
            "edition_id": updated_edition.product_id,
            "sku": updated_edition.sku,
            "stock_on_hand": updated_edition.stock_on_hand,
            "available_stock": updated_edition.get_available_stock(),
        }
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/orders")
def get_orders(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    inventory_service: InventoryService = Depends(get_inventory_service),
    order_repo: OrderRepository = Depends(get_order_repo),
):
    controller = AdminController(inventory_service, order_repo)
    orders = controller.get_orders(limit=limit, offset=offset)
    return {"total": len(orders), "orders": orders}


@router.post("/orders/{order_id}/dispatch")
def dispatch_order(
    order_id: str,
    request: DispatchOrderWebRequest,
    inventory_service: InventoryService = Depends(get_inventory_service),
    order_repo: OrderRepository = Depends(get_order_repo),
):
    controller = AdminController(inventory_service, order_repo)
    try:
        order = controller.dispatch_order(
            order_id=int(order_id), carrier_name=request.carrier
        )
        return serialize_order(order)
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (InvalidOrderStateException, DroneOverweightException, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/orders/{order_id}/delivered")
def mark_delivered(
    order_id: str,
    inventory_service: InventoryService = Depends(get_inventory_service),
):
    try:
        order = inventory_service.mark_delivered(int(order_id))
        return serialize_order(order)
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (InvalidOrderStateException, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/reports/revenue")
def get_revenue_report(
    inventory_service: InventoryService = Depends(get_inventory_service),
    order_repo: OrderRepository = Depends(get_order_repo),
):
    controller = AdminController(inventory_service, order_repo)
    return controller.get_revenue_report()

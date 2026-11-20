"""
Thin Web Layer: Payment & Orders Router
Điều phối HTTP Requests cho Xác nhận thanh toán VietQR, Webhook và Cập nhật trạng thái đơn.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from ..presentation.controller.PaymentController import PaymentController
from ..presentation.dependencies import get_payment_service, get_inventory_service
from ..application.services.payment_service import PaymentService
from ..application.services.inventory_service import InventoryService
from ..domain.exceptions import EntityNotFoundException, InvalidOrderStateException
from .schemas import ConfirmPaymentWebRequest
from .serializers import serialize_order

router = APIRouter(tags=["Payments & Orders"])


@router.post("/payments/confirm")
def confirm_payment(
    request: ConfirmPaymentWebRequest,
    payment_service: PaymentService = Depends(get_payment_service),
):
    controller = PaymentController(payment_service)
    try:
        order = controller.confirm_payment(
            order_id=int(request.order_id),
            transaction_code=request.transaction_code,
        )
        return serialize_order(order)
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (InvalidOrderStateException, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/payments/webhook")
def receive_bank_webhook(
    payload: Dict[str, Any],
    payment_service: PaymentService = Depends(get_payment_service),
):
    controller = PaymentController(payment_service)
    result = controller.receive_bank_webhook(payload)
    if not result.get("success"):
        return {"status": "ignored", "detail": result.get("message")}
    return {"status": "success", "data": result}


@router.get("/orders/{order_id}/status")
def get_order_payment_status(
    order_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
    inventory_service: InventoryService = Depends(get_inventory_service),
):
    controller = PaymentController(payment_service, inventory_service)
    try:
        return controller.get_order_payment_status(order_id)
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/orders/{order_id}/delivered")
def mark_order_delivered(
    order_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
    inventory_service: InventoryService = Depends(get_inventory_service),
):
    controller = PaymentController(payment_service, inventory_service)
    try:
        order = controller.mark_order_delivered(order_id)
        return serialize_order(order)
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (InvalidOrderStateException, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

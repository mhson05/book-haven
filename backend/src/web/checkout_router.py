"""
Thin Web Layer: Checkout Router
Điều phối HTTP Requests cho Quy trình Đặt hàng và Tra cứu Giao vận.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..presentation.controller.CheckoutController import CheckoutController
from ..presentation.dependencies import get_checkout_service
from ..application.services.checkout_service import CheckoutService
from ..domain.exceptions import (
    OutOfStockException,
    DroneOverweightException,
    DomainException,
)
from .cart_router import resolve_customer_id
from .schemas import CheckoutWebRequest
from .serializers import serialize_order, serialize_shipping_options

router = APIRouter(tags=["Checkout & Shipping"])


@router.post("/checkout")
def execute_checkout(
    request: CheckoutWebRequest,
    customer_id: int = Depends(resolve_customer_id),
    checkout_service: CheckoutService = Depends(get_checkout_service),
):
    controller = CheckoutController(checkout_service)
    try:
        try:
            cid = int(request.cart_id)
        except Exception:
            cid = 1

        order = controller.execute_checkout(
            customer_id=customer_id,
            cart_id=cid,
            receiver_name=request.receiver_name,
            receiver_phone=request.receiver_phone,
            shipping_address=request.shipping_address,
            payment_method=request.payment_method,
            carrier=request.carrier,
            voucher_code=request.voucher_code,
        )
        return serialize_order(order)
    except (OutOfStockException, DroneOverweightException, ValueError, DomainException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/shipping/options")
def get_shipping_options(
    cart_id: Optional[str] = Query(None, description="Mã giỏ hàng để tính trọng lượng thực"),
    checkout_service: CheckoutService = Depends(get_checkout_service),
):
    controller = CheckoutController(checkout_service)
    raw_options = controller.get_shipping_options(cart_id)
    return serialize_shipping_options(raw_options)

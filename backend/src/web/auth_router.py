"""
Thin Web Layer: Auth Router
Điều phối HTTP Requests cho Xác thực tài khoản, Đăng ký và Hồ sơ người dùng.
"""
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status

from ..presentation.controller.AuthController import AuthController
from ..presentation.dependencies import get_auth_service, get_order_repo, get_current_user
from ..application.services.auth_service import AuthService
from ..infrastructure.repositories.order_repository import OrderRepository
from ..domain.entities.user import User
from ..domain.entities.order import Order
from ..domain.exceptions import DomainException
from .schemas import LoginWebRequest, RegisterWebRequest
from .serializers import serialize_token, serialize_user_profile

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _serialize_order_summary(order: Order) -> Dict[str, Any]:
    created_at_val = order.created_at
    if isinstance(created_at_val, datetime):
        created_at_val = created_at_val.strftime("%Y-%m-%d %H:%M:%S")

    items_list = []
    for it in order.items:
        title = getattr(it, "product_name_snapshot", "") or getattr(it, "title_snapshot", "")
        binding = getattr(it, "product_kind_snapshot", "") or getattr(it, "binding_type_snapshot", "")
        subtotal = it.calculate_subtotal() if hasattr(it, "calculate_subtotal") else it.unit_price_at_purchase * it.quantity
        items_list.append({
            "title": title,
            "binding_type": binding,
            "quantity": it.quantity,
            "unit_price": it.unit_price_at_purchase,
            "subtotal": subtotal,
        })

    carrier_val = getattr(order.carrier, "value", str(order.carrier)) if order.carrier else None
    status_val = getattr(order.status, "value", str(order.status))

    return {
        "order_id": order.order_id,
        "created_at": created_at_val,
        "status": status_val,
        "final_amount": order.final_amount,
        "carrier": carrier_val,
        "tracking_code": order.tracking_code,
        "receiver_name": order.receiver_name,
        "shipping_address": order.shipping_address,
        "items_count": len(order.items),
        "items": items_list,
    }


@router.post("/login")
def login(
    request: LoginWebRequest,
    auth_service: AuthService = Depends(get_auth_service),
    order_repo: OrderRepository = Depends(get_order_repo),
):
    controller = AuthController(auth_service, order_repo)
    try:
        token, user = controller.login(request.username, request.password)
        return serialize_token(token, user)
    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/register")
def register(
    request: RegisterWebRequest,
    auth_service: AuthService = Depends(get_auth_service),
    order_repo: OrderRepository = Depends(get_order_repo),
):
    controller = AuthController(auth_service, order_repo)
    try:
        token, user = controller.register(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            phone=request.phone,
            shipping_address=request.shipping_address,
        )
        return serialize_token(token, user)
    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    order_repo: OrderRepository = Depends(get_order_repo),
):
    controller = AuthController(auth_service, order_repo)
    user = controller.get_profile(str(current_user.user_id))
    return serialize_user_profile(user)


@router.get("/orders")
def get_user_orders(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    order_repo: OrderRepository = Depends(get_order_repo),
):
    controller = AuthController(auth_service, order_repo)
    orders = controller.get_user_orders(str(current_user.user_id))
    return [_serialize_order_summary(o) for o in orders]

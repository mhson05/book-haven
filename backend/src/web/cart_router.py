"""
Thin Web Layer: Cart Router
Điều phối HTTP Requests cho Giỏ hàng thông qua CartController và Serializer.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status

from ..presentation.controller.CartController import CartController
from ..presentation.dependencies import get_cart_service, get_current_user_optional
from ..application.services.cart_service import CartService
from ..domain.entities.user import User
from ..domain.exceptions import OutOfStockException, EntityNotFoundException
from .schemas import AddToCartWebRequest, UpdateCartItemWebRequest
from .serializers import serialize_cart

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])


def resolve_customer_id(
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_customer_id: Optional[str] = Header(None),
) -> int:
    if current_user:
        try:
            return int(current_user.user_id)
        except Exception:
            return 2
    if x_customer_id and x_customer_id.strip():
        try:
            return int(x_customer_id.strip())
        except ValueError:
            return 2
    return 2


@router.get("")
def get_cart(
    customer_id: int = Depends(resolve_customer_id),
    cart_service: CartService = Depends(get_cart_service),
):
    controller = CartController(cart_service)
    cart = controller.get_cart(customer_id)
    return serialize_cart(cart)


@router.post("/items")
def add_to_cart(
    request: AddToCartWebRequest,
    customer_id: int = Depends(resolve_customer_id),
    cart_service: CartService = Depends(get_cart_service),
):
    controller = CartController(cart_service)
    try:
        try:
            eid = int(request.edition_id)
        except Exception:
            eid = 1
        cart = controller.add_to_cart(
            customer_id=customer_id, product_id=eid, quantity=request.quantity
        )
        return serialize_cart(cart)
    except (OutOfStockException, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/items/{edition_id}")
def update_item_quantity(
    edition_id: str,
    request: UpdateCartItemWebRequest,
    customer_id: int = Depends(resolve_customer_id),
    cart_service: CartService = Depends(get_cart_service),
):
    controller = CartController(cart_service)
    try:
        eid = int(edition_id)
        cart = controller.update_item_quantity(
            customer_id=customer_id, product_id=eid, quantity=request.quantity
        )
        return serialize_cart(cart)
    except (OutOfStockException, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/items/{edition_id}")
def remove_item(
    edition_id: str,
    customer_id: int = Depends(resolve_customer_id),
    cart_service: CartService = Depends(get_cart_service),
):
    controller = CartController(cart_service)
    try:
        eid = int(edition_id)
    except Exception:
        eid = 1
    cart = controller.remove_item(customer_id=customer_id, product_id=eid)
    return serialize_cart(cart)


@router.delete("")
def clear_cart(
    customer_id: int = Depends(resolve_customer_id),
    cart_service: CartService = Depends(get_cart_service),
):
    controller = CartController(cart_service)
    cart = controller.clear_cart(customer_id)
    return serialize_cart(cart)

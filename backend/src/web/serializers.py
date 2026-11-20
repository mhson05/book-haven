"""
Thin Web Layer: Serializers
Chuyển đổi các Domain Entities và Runtime Objects sang cấu trúc JSON phản hồi cho Client/Frontend.
Đảm bảo tính tương thích 100% với Frontend React và Test Suite mà không làm vấy bẩn Domain/Controller.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..domain.entities.cart import Cart
from ..domain.entities.order import Order
from ..domain.entities.user import User
from ..domain.entities.product import Product
from ..application.services.search_result import SearchResult
from ..application.services.chatbot_result import ChatbotResult


def serialize_cart(cart: Cart) -> Dict[str, Any]:
    """Chuyển đổi Domain Entity Cart thành CartResponse JSON."""
    items_data = []
    for item in cart.items:
        prod = item.product
        items_data.append({
            "cart_item_id": str(item.cart_item_id or ""),
            "edition_id": str(item.product_id or (prod.product_id if prod else "")),
            "book_id": str(getattr(prod, "book_id", "") or item.product_id or ""),
            "title": prod.name if prod else "",
            "sku": prod.sku if prod else "",
            "binding_type": getattr(prod, "binding_type", "Standard"),
            "isbn13": getattr(prod, "isbn13", ""),
            "unit_price": prod.unit_price if prod else 0,
            "weight_gram": prod.weight_gram if prod else 0,
            "quantity": item.quantity,
            "subtotal": item.calculate_line_total(),
            "cover_image": getattr(prod, "cover_image", None),
            "available_stock": prod.get_available_stock() if prod else 0,
        })

    return {
        "cart_id": str(cart.cart_id or ""),
        "customer_id": str(cart.customer_id or ""),
        "subtotal": cart.calculate_subtotal(),
        "total_weight_grams": cart.calculate_total_weight(),
        "items": items_data,
    }


def serialize_order(order: Order, vietqr_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Chuyển đổi Domain Entity Order thành OrderResponse JSON."""
    created_at_str = None
    if order.created_at:
        if isinstance(order.created_at, datetime):
            created_at_str = order.created_at.strftime("%Y-%m-%d %H:%M:%S")
        else:
            created_at_str = str(order.created_at)

    items_data = []
    for it in order.items:
        items_data.append({
            "order_item_id": str(it.order_item_id or ""),
            "edition_id": str(it.product_id),
            "title": it.product_name_snapshot,
            "sku": it.sku_snapshot,
            "binding_type": it.product_kind_snapshot,
            "isbn13": "",
            "unit_price": it.unit_price_at_purchase,
            "quantity": it.quantity,
            "weight_gram": it.weight_gram_snapshot,
            "subtotal": it.calculate_subtotal(),
        })

    qr_data = getattr(order, "vietqr_data", None) or vietqr_data
    expires_at = getattr(order, "reservation_expires_at", None)

    return {
        "order_id": str(order.order_id or ""),
        "customer_id": str(order.customer_id or ""),
        "receiver_name": order.receiver_name,
        "receiver_phone": order.receiver_phone,
        "shipping_address": order.shipping_address,
        "payment_method": order.payment_method,
        "carrier": order.carrier,
        "total_amount": order.total_amount,
        "shipping_fee": order.shipping_fee,
        "discount_amount": order.discount_amount,
        "final_amount": order.final_amount,
        "status": order.status,
        "tracking_code": order.tracking_code,
        "created_at": created_at_str,
        "items": items_data,
        "vietqr_data": qr_data,
        "reservation_expires_at": expires_at,
    }


def serialize_shipping_options(shipping_options: Dict[str, Any]) -> Dict[str, Any]:
    """Chuyển đổi kết quả tra cứu cước sang ShippingOptionsResponse JSON."""
    raw_options = shipping_options.get("options", [])
    formatted_options = []
    for opt in raw_options:
        formatted_options.append({
            "carrier_code": opt.get("code") or opt.get("carrier_code"),
            "carrier_name": opt.get("name") or opt.get("carrier_name"),
            "fee": opt.get("fee", 0),
            "estimated_time": opt.get("estimated_time", ""),
            "is_available": opt.get("is_eligible", opt.get("is_available", True)),
            "disabled_reason": opt.get("ineligible_reason") or opt.get("disabled_reason"),
        })

    return {
        "total_weight_grams": shipping_options.get("calculated_package_weight_grams", 0),
        "options": formatted_options,
    }


def serialize_token(token: str, user: User) -> Dict[str, Any]:
    """Chuyển đổi token và Domain Entity User thành TokenResponse JSON."""
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(user.user_id or ""),
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
    }


def serialize_user_profile(user: User) -> Dict[str, Any]:
    """Chuyển đổi Domain Entity User thành UserProfileResponse JSON."""
    return {
        "user_id": str(user.user_id or ""),
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role,
        "shipping_address": user.shipping_address,
        "loyalty_points": user.loyalty_points,
    }


def serialize_search_result(search_result: SearchResult) -> Dict[str, Any]:
    """Chuyển đổi Runtime Class SearchResult thành SearchResponse JSON."""
    return {
        "total_found": search_result.total_found,
        "search_mode": search_result.search_mode,
        "results": search_result.results,
    }


def serialize_chatbot_result(chatbot_result: ChatbotResult) -> Dict[str, Any]:
    """Chuyển đổi Runtime Class ChatbotResult thành ChatMessageResponse JSON."""
    return {
        "reply": chatbot_result.reply,
        "suggested_books": chatbot_result.suggested_books,
    }

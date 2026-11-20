"""
Thin Web Layer: Request Schemas (Pydantic)
Xác thực và phân giải cấu trúc dữ liệu JSON từ HTTP Request của Client.
Tách biệt hoàn toàn với tầng Domain và Controller thuần OOP.
"""
from typing import Any, Optional
from pydantic import BaseModel, Field


class LoginWebRequest(BaseModel):
    username: str
    password: str


class RegisterWebRequest(BaseModel):
    username: str
    password: str
    email: str
    full_name: str
    phone: Optional[str] = None
    shipping_address: Optional[str] = None


class AddToCartWebRequest(BaseModel):
    edition_id: Any
    quantity: int = Field(default=1, ge=1)


class UpdateCartItemWebRequest(BaseModel):
    quantity: int = Field(ge=0)


class CheckoutWebRequest(BaseModel):
    cart_id: str
    receiver_name: str
    receiver_phone: str
    shipping_address: str
    payment_method: str = "VIETQR"
    carrier: str = "GHN_STANDARD"
    voucher_code: Optional[str] = None


class SemanticSearchWebRequest(BaseModel):
    query: str
    limit: int = 5


class ConfirmPaymentWebRequest(BaseModel):
    order_id: str
    transaction_code: Optional[str] = None


class RestockWebRequest(BaseModel):
    edition_id: str
    quantity: int = Field(gt=0)


class DispatchOrderWebRequest(BaseModel):
    carrier: str = "HANOI_DRONE"


class ChatMessageWebRequest(BaseModel):
    message: str

"""
Application Service: AuthService
Quản lý xác thực người dùng, băm mật khẩu Bcrypt, phát hành & kiểm tra JSON Web Token (JWT).
Tuân thủ chuẩn UML Visual Paradigm: Nhận tham số nguyên thủy, trả về Tuple (token, user) và Domain Entity User.
"""
import os
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple

from ...domain.entities.user import User
from ...domain.entities.customer import Customer
from ...domain.exceptions import DomainException, EntityNotFoundException
from ...infrastructure.repositories.user_repository import UserRepository

DEFAULT_SECRET = "bookhaven-ecommerce-secret-key-pttkhttt-2026-ptit-security"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


class AuthService:
    def __init__(self, user_repo: UserRepository, secret_key: Optional[str] = None):
        self.user_repo = user_repo
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", DEFAULT_SECRET)

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    def create_access_token(self, user_id: str, username: str, role: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        payload = {
            "sub": str(user_id),
            "username": username,
            "role": role,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, self.secret_key, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise DomainException("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.")
        except jwt.InvalidTokenError:
            raise DomainException("Token xác thực không hợp lệ.")

    def login(self, username: str, password: str) -> Tuple[str, User]:
        """
        Xác thực đăng nhập và trả về Tuple (access_token, user).
        Khớp hoàn toàn với mô hình phân tích thiết kế của thầy Quế và bạn NhiCT.
        """
        user = self.user_repo.get_by_username(username)
        if not user:
            user = self.user_repo.get_by_email(username)
        if not user or not self.verify_password(password, user.password_hash):
            raise DomainException("Tài khoản hoặc mật khẩu không chính xác.")

        role_str = (
            user.role
            if isinstance(user.role, str)
            else getattr(user.role, "value", str(user.role))
        )
        token = self.create_access_token(str(user.user_id), user.username, role_str)
        return token, user

    def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str] = None,
        shipping_address: Optional[str] = None,
    ) -> Tuple[str, User]:
        """
        Đăng ký tài khoản khách hàng mới và trả về Tuple (access_token, user).
        """
        existing_username = self.user_repo.get_by_username(username)
        if existing_username:
            raise DomainException(f"Tên tài khoản '{username}' đã được đăng ký.")

        existing_email = self.user_repo.get_by_email(email)
        if existing_email:
            raise DomainException(f"Địa chỉ email '{email}' đã được sử dụng.")

        password_hash = self.hash_password(password)

        new_customer = Customer(
            username=username,
            password_hash=password_hash,
            email=email,
            full_name=full_name,
            phone=phone,
            role="CUSTOMER",
            shipping_address=shipping_address or "",
            loyalty_points=0,
        )
        saved_customer = self.user_repo.create_customer(new_customer)

        role_str = "CUSTOMER"
        token = self.create_access_token(
            str(saved_customer.user_id), saved_customer.username, role_str
        )
        return token, saved_customer

    def get_profile(self, user_id: str) -> User:
        """Lấy thông tin thực thể User."""
        uid = int(user_id) if str(user_id).isdigit() else user_id
        user = self.user_repo.get_by_id(uid)
        if not user:
            raise EntityNotFoundException("User", str(user_id))
        return user

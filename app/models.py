from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime, date, time

class UserRole(str, Enum):
    MASTER = "master"
    ADMIN = "admin"
    PARTNER = "partner"
    USER = "user"

class VendorType(str, Enum):
    MILK = "milk"
    LAUNDRY = "laundry" 
    FOOD = "food"
    CLEANING = "cleaning"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

class UserBase(BaseModel):
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.USER
    community_id: Optional[str] = None
    apartment_number: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class CommunityBase(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    description: Optional[str] = None

class CommunityCreate(CommunityBase):
    pass

class CommunityResponse(CommunityBase):
    id: str
    created_at: datetime
    updated_at: datetime

class VendorBase(BaseModel):
    name: str
    type: VendorType
    community_id: str
    admin_id: Optional[str] = None
    description: Optional[str] = None
    operating_hours: Optional[dict] = None

class VendorCreate(VendorBase):
    pass

class VendorResponse(VendorBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ProductBase(BaseModel):
    vendor_id: str
    category_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float
    unit: Optional[str] = None
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: str
    is_available: bool
    created_at: datetime
    updated_at: datetime

class OrderBase(BaseModel):
    user_id: str
    vendor_id: str
    partner_id: Optional[str] = None
    total_amount: float
    delivery_address: Optional[str] = None
    delivery_date: Optional[date] = None
    delivery_time: Optional[time] = None
    special_instructions: Optional[str] = None

class OrderCreate(OrderBase):
    items: List[dict]

class OrderResponse(OrderBase):
    id: str
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class PaymentBase(BaseModel):
    order_id: str
    user_id: str
    amount: float
    payment_method: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: str
    status: PaymentStatus
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
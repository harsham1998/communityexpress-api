from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# User Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    apartment_number: Optional[str] = None
    community_id: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    apartment_number: Optional[str] = None
    role: str
    community_id: Optional[str] = None
    community_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Community Models
class CommunityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    postal_code: Optional[str] = None

class CommunityResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str
    postal_code: Optional[str] = None
    community_code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

# Vendor Models
class VendorCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    community_id: str
    admin_id: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    operating_hours: Optional[Dict[str, str]] = None

class VendorResponse(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None
    community_id: str
    community_name: Optional[str] = None
    admin_id: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    operating_hours: Optional[Dict[str, str]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

# Product Models
class ProductCreate(BaseModel):
    vendor_id: str
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool = True

class ProductResponse(BaseModel):
    id: str
    vendor_id: str
    vendor_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool
    created_at: datetime
    updated_at: datetime

# Order Models
class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int
    unit_price: float
    special_instructions: Optional[str] = None

class OrderCreate(BaseModel):
    vendor_id: str
    items: List[OrderItemCreate]
    delivery_address: str
    delivery_instructions: Optional[str] = None
    payment_method: Optional[str] = None

class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    special_instructions: Optional[str] = None

class OrderResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    vendor_id: str
    vendor_name: str
    order_number: str
    status: OrderStatus
    items: List[OrderItemResponse]
    subtotal: float
    delivery_charge: float
    tax_amount: float
    total_amount: float
    delivery_address: str
    delivery_instructions: Optional[str] = None
    payment_method: Optional[str] = None
    payment_status: str
    created_at: datetime
    updated_at: datetime
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

# Payment Models
class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentCreate(BaseModel):
    order_id: str
    amount: float
    payment_method: str
    payment_reference: Optional[str] = None

class PaymentResponse(BaseModel):
    id: str
    order_id: str
    user_id: str
    amount: float
    payment_method: str
    payment_reference: Optional[str] = None
    status: PaymentStatus
    transaction_id: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
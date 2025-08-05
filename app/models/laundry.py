from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

# Laundry specific models

class LaundryVendorCreate(BaseModel):
    business_name: str
    description: Optional[str] = None
    pickup_time_start: str = "08:00"
    pickup_time_end: str = "18:00"  
    delivery_time_hours: int = 24
    minimum_order_amount: float = 100.0
    pickup_charge: float = 20.0
    delivery_charge: float = 30.0
    service_areas: List[str] = []

class LaundryVendorUpdate(BaseModel):
    business_name: Optional[str] = None
    description: Optional[str] = None
    pickup_time_start: Optional[str] = None
    pickup_time_end: Optional[str] = None
    delivery_time_hours: Optional[int] = None
    minimum_order_amount: Optional[float] = None
    pickup_charge: Optional[float] = None
    delivery_charge: Optional[float] = None
    service_areas: Optional[List[str]] = None
    is_active: Optional[bool] = None

class LaundryVendorResponse(BaseModel):
    id: str
    vendor_id: str
    business_name: str
    description: Optional[str] = None
    pickup_time_start: str
    pickup_time_end: str
    delivery_time_hours: int
    minimum_order_amount: float
    pickup_charge: float
    delivery_charge: float
    service_areas: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class LaundryItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    price_per_piece: float
    estimated_time_hours: int = 24
    image_url: Optional[str] = None

class LaundryItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price_per_piece: Optional[float] = None
    estimated_time_hours: Optional[int] = None
    is_available: Optional[bool] = None
    image_url: Optional[str] = None

class LaundryItemResponse(BaseModel):
    id: str
    laundry_vendor_id: str
    name: str
    description: Optional[str] = None
    category: str
    price_per_piece: float
    estimated_time_hours: int
    is_available: bool
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class LaundryOrderItemCreate(BaseModel):
    laundry_item_id: str
    quantity: int = Field(gt=0)
    special_instructions: Optional[str] = None

class LaundryOrderItemResponse(BaseModel):
    id: str
    laundry_item_id: str
    quantity: int
    unit_price: float
    total_price: float
    special_instructions: Optional[str] = None
    item_name: str
    item_category: str
    item_description: Optional[str] = None

class LaundryOrderCreate(BaseModel):
    laundry_vendor_id: str
    pickup_address: str
    pickup_date: date
    pickup_time_slot: str
    pickup_instructions: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_instructions: Optional[str] = None
    items: List[LaundryOrderItemCreate]

class LaundryOrderUpdate(BaseModel):
    status: Optional[str] = None
    pickup_instructions: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_instructions: Optional[str] = None
    estimated_delivery_date: Optional[date] = None
    estimated_delivery_time: Optional[str] = None

class LaundryOrderResponse(BaseModel):
    id: str
    user_id: str
    laundry_vendor_id: str
    order_number: str
    pickup_address: str
    pickup_date: date
    pickup_time_slot: str
    pickup_instructions: Optional[str] = None
    delivery_address: Optional[str] = None
    estimated_delivery_date: Optional[date] = None
    estimated_delivery_time: Optional[str] = None
    delivery_instructions: Optional[str] = None
    status: str
    subtotal: float
    pickup_charge: float
    delivery_charge: float
    tax_amount: float
    total_amount: float
    payment_status: str
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: List[LaundryOrderItemResponse]
    vendor_business_name: str
    user_name: str
    user_phone: Optional[str] = None

class LaundryPaymentRequest(BaseModel):
    payment_method: str
    payment_reference: Optional[str] = None

class LaundryPaymentResponse(BaseModel):
    success: bool
    payment_reference: str
    message: str

class LaundryVendorStats(BaseModel):
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    in_process_orders: int
    ready_orders: int
    delivered_orders: int
    cancelled_orders: int
    today_revenue: float
    monthly_revenue: float
    active_items: int

class LaundryVendorDashboard(BaseModel):
    stats: LaundryVendorStats
    recent_orders: List[LaundryOrderResponse]

class LaundryUserStats(BaseModel):
    total_orders: int
    pending_orders: int
    delivered_orders: int
    total_spent: float
    favorite_vendor: Optional[str] = None
    recent_orders: List[LaundryOrderResponse]
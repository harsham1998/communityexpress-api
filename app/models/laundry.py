from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, time
from decimal import Decimal

# Laundry Vendor Models
class LaundryVendorCreate(BaseModel):
    vendor_id: str
    business_name: str
    description: Optional[str] = None
    pickup_time_start: Optional[time] = time(8, 0)
    pickup_time_end: Optional[time] = time(18, 0)
    delivery_time_hours: Optional[int] = 24
    minimum_order_amount: Optional[Decimal] = Decimal('0.00')
    pickup_charge: Optional[Decimal] = Decimal('0.00')
    delivery_charge: Optional[Decimal] = Decimal('0.00')
    service_areas: Optional[List[str]] = []

class LaundryVendorUpdate(BaseModel):
    business_name: Optional[str] = None
    description: Optional[str] = None
    pickup_time_start: Optional[time] = None
    pickup_time_end: Optional[time] = None
    delivery_time_hours: Optional[int] = None
    minimum_order_amount: Optional[Decimal] = None
    pickup_charge: Optional[Decimal] = None
    delivery_charge: Optional[Decimal] = None
    service_areas: Optional[List[str]] = None
    is_active: Optional[bool] = None

class LaundryVendorResponse(BaseModel):
    id: str
    vendor_id: str
    business_name: str
    description: Optional[str]
    pickup_time_start: time
    pickup_time_end: time
    delivery_time_hours: int
    minimum_order_amount: Decimal
    pickup_charge: Decimal
    delivery_charge: Decimal
    service_areas: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

# Laundry Item Models
class LaundryItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = Field(..., description="Category like 'wash', 'dry_clean', 'iron', etc.")
    price_per_piece: Decimal = Field(..., gt=0)
    estimated_time_hours: Optional[int] = 24
    image_url: Optional[str] = None

class LaundryItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price_per_piece: Optional[Decimal] = None
    estimated_time_hours: Optional[int] = None
    is_available: Optional[bool] = None
    image_url: Optional[str] = None

class LaundryItemResponse(BaseModel):
    id: str
    laundry_vendor_id: str
    name: str
    description: Optional[str]
    category: str
    price_per_piece: Decimal
    estimated_time_hours: int
    is_available: bool
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime

# Laundry Order Models
class LaundryOrderItemCreate(BaseModel):
    laundry_item_id: str
    quantity: int = Field(..., gt=0)
    special_instructions: Optional[str] = None

class LaundryOrderCreate(BaseModel):
    laundry_vendor_id: str
    pickup_address: str
    pickup_date: date
    pickup_time_slot: str = Field(..., description="Time slot like '09:00-12:00'")
    pickup_instructions: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_instructions: Optional[str] = None
    items: List[LaundryOrderItemCreate]

class LaundryOrderUpdate(BaseModel):
    status: Optional[str] = None
    pickup_address: Optional[str] = None
    pickup_date: Optional[date] = None
    pickup_time_slot: Optional[str] = None
    pickup_instructions: Optional[str] = None
    delivery_address: Optional[str] = None
    estimated_delivery_date: Optional[date] = None
    estimated_delivery_time: Optional[str] = None
    delivery_instructions: Optional[str] = None

class LaundryOrderItemResponse(BaseModel):
    id: str
    laundry_item_id: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    special_instructions: Optional[str]
    # Include item details
    item_name: str
    item_category: str
    item_description: Optional[str]

class LaundryOrderResponse(BaseModel):
    id: str
    user_id: str
    laundry_vendor_id: str
    order_number: str
    pickup_address: str
    pickup_date: date
    pickup_time_slot: str
    pickup_instructions: Optional[str]
    delivery_address: Optional[str]
    estimated_delivery_date: Optional[date]
    estimated_delivery_time: Optional[str]
    delivery_instructions: Optional[str]
    status: str
    subtotal: Decimal
    pickup_charge: Decimal
    delivery_charge: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    payment_status: str
    payment_method: Optional[str]
    payment_reference: Optional[str]
    confirmed_at: Optional[datetime]
    picked_up_at: Optional[datetime]
    ready_at: Optional[datetime]
    delivered_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    items: List[LaundryOrderItemResponse]
    # Include vendor details
    vendor_business_name: str
    # Include user details
    user_name: str
    user_phone: Optional[str]

# Payment Models
class LaundryPaymentRequest(BaseModel):
    payment_method: str = Field(..., description="Payment method like 'dummy', 'card', 'upi', etc.")
    payment_reference: Optional[str] = None

class LaundryPaymentResponse(BaseModel):
    success: bool
    payment_reference: str
    message: str

# Dashboard Models
class LaundryVendorDashboard(BaseModel):
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    in_process_orders: int
    ready_orders: int
    delivered_orders: int
    cancelled_orders: int
    today_revenue: Decimal
    monthly_revenue: Decimal
    active_items: int
    recent_orders: List[LaundryOrderResponse]

class LaundryUserStats(BaseModel):
    total_orders: int
    pending_orders: int
    delivered_orders: int
    total_spent: Decimal
    favorite_vendor: Optional[str]
    recent_orders: List[LaundryOrderResponse]
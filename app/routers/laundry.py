from fastapi import APIRouter, HTTPException, status, Depends, Query, Header, Request
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from app.models.laundry import (
    LaundryVendorCreate, LaundryVendorUpdate, LaundryVendorResponse,
    LaundryItemCreate, LaundryItemUpdate, LaundryItemResponse,
    LaundryOrderCreate, LaundryOrderUpdate, LaundryOrderResponse,
    LaundryPaymentRequest, LaundryPaymentResponse,
    LaundryVendorDashboard, LaundryVendorStats, LaundryUserStats
)
from app.models import UserResponse
from app.auth import get_current_user
from app.database import get_supabase_client

router = APIRouter(prefix="/laundry", tags=["laundry"])

# Laundry Vendor Management Endpoints

def get_current_user_or_testing(
    request: Request,
    x_testing: Optional[str] = Header(None)
):
    """Get current user or allow testing mode only for localhost"""
    from dateutil import parser
    
    # Check if request is from localhost and testing header is present
    host = request.client.host if request.client else ""
    is_localhost = host in ["127.0.0.1", "localhost", "::1"]
    
    if is_localhost and x_testing == "true":
        # Return a mock user for testing (only in localhost)
        return UserResponse(
            id="test-user-id",
            email="test@testing.com",
            first_name="Test",
            last_name="User",
            role="master",
            community_id="test-community-id",
            is_active=True,
            created_at=parser.parse("2024-01-01T00:00:00Z"),
            updated_at=parser.parse("2024-01-01T00:00:00Z")
        )
    
    # For non-localhost or without testing header, require authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated"
    )

@router.post("/vendors", response_model=LaundryVendorResponse)
async def create_laundry_vendor(
    vendor_data: LaundryVendorCreate,
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Create a new laundry vendor profile"""
    if current_user.role not in ["master", "vendor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only masters and vendors can create laundry vendor profiles"
        )
    
    supabase = get_supabase_client()
    
    try:
        # Insert laundry vendor data
        vendor_insert_data = {
            "vendor_id": vendor_data.vendor_id,
            "business_name": vendor_data.business_name,
            "description": vendor_data.description,
            "pickup_time_start": vendor_data.pickup_time_start.strftime("%H:%M:%S"),
            "pickup_time_end": vendor_data.pickup_time_end.strftime("%H:%M:%S"),
            "delivery_time_hours": vendor_data.delivery_time_hours,
            "minimum_order_amount": float(vendor_data.minimum_order_amount),
            "pickup_charge": float(vendor_data.pickup_charge),
            "delivery_charge": float(vendor_data.delivery_charge),
            "service_areas": vendor_data.service_areas
        }
        
        response = supabase.table("laundry_vendors").insert(vendor_insert_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create laundry vendor"
            )
        
        created_vendor = response.data[0]
        return LaundryVendorResponse(**created_vendor)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create laundry vendor: {str(e)}"
        )

@router.get("/vendors", response_model=List[LaundryVendorResponse])
async def get_laundry_vendors(
    community_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Get all laundry vendors (optionally filtered by community)"""
    supabase = get_supabase_client()
    
    try:
        if community_id or (current_user.community_id and current_user.role == "user"):
            # If we need to filter by community, we need to join with vendors table
            query = supabase.table("laundry_vendors").select("""
                *,
                vendors!inner(
                    community_id
                )
            """)
            
            if community_id:
                query = query.eq("vendors.community_id", community_id)
            elif current_user.community_id and current_user.role == "user":
                query = query.eq("vendors.community_id", current_user.community_id)
        else:
            # If no community filter needed, just get laundry_vendors
            query = supabase.table("laundry_vendors").select("*")
            
        if is_active is not None:
            query = query.eq("is_active", is_active)
            
        response = query.execute()
        
        return [LaundryVendorResponse(**vendor) for vendor in response.data]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch laundry vendors: {str(e)}"
        )

@router.get("/vendors/{vendor_id}", response_model=LaundryVendorResponse)
async def get_laundry_vendor(
    vendor_id: str,
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Get a specific laundry vendor by ID"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("laundry_vendors").select("*").eq("id", vendor_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Laundry vendor not found"
            )
        
        return LaundryVendorResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch laundry vendor: {str(e)}"
        )

@router.put("/vendors/{vendor_id}", response_model=LaundryVendorResponse)
async def update_laundry_vendor(
    vendor_id: str,
    vendor_data: LaundryVendorUpdate,
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Update a laundry vendor profile"""
    supabase = get_supabase_client()
    
    # Check if user owns this vendor or is a master
    if current_user.role not in ["master"]:
        # Check if current user owns this vendor
        vendor_check = supabase.table("laundry_vendors").select("vendor_id").eq("id", vendor_id).execute()
        if not vendor_check.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
        
        # Check if the vendor belongs to current user
        user_vendor_check = supabase.table("vendors").select("user_id").eq("id", vendor_check.data[0]["vendor_id"]).execute()
        if not user_vendor_check.data or user_vendor_check.data[0]["user_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    try:
        update_data = {}
        for field, value in vendor_data.dict(exclude_unset=True).items():
            if field in ["pickup_time_start", "pickup_time_end"] and value:
                update_data[field] = value.strftime("%H:%M:%S")
            elif field in ["minimum_order_amount", "pickup_charge", "delivery_charge"] and value is not None:
                update_data[field] = float(value)
            else:
                update_data[field] = value
        
        response = supabase.table("laundry_vendors").update(update_data).eq("id", vendor_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Laundry vendor not found"
            )
        
        return LaundryVendorResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update laundry vendor: {str(e)}"
        )

# Laundry Items Management Endpoints

@router.post("/vendors/{vendor_id}/items", response_model=LaundryItemResponse)
async def create_laundry_item(
    vendor_id: str,
    item_data: LaundryItemCreate,
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Create a new laundry item for a vendor"""
    supabase = get_supabase_client()
    
    # Verify vendor ownership
    if current_user.role not in ["master"]:
        vendor_check = supabase.table("laundry_vendors").select("vendor_id").eq("id", vendor_id).execute()
        if not vendor_check.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
        
        user_vendor_check = supabase.table("vendors").select("user_id").eq("id", vendor_check.data[0]["vendor_id"]).execute()
        if not user_vendor_check.data or user_vendor_check.data[0]["user_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    try:
        item_insert_data = {
            "laundry_vendor_id": vendor_id,
            "name": item_data.name,
            "description": item_data.description,
            "category": item_data.category,
            "price_per_piece": float(item_data.price_per_piece),
            "estimated_time_hours": item_data.estimated_time_hours,
            "image_url": item_data.image_url
        }
        
        response = supabase.table("laundry_items").insert(item_insert_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create laundry item"
            )
        
        return LaundryItemResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create laundry item: {str(e)}"
        )

@router.get("/vendors/{vendor_id}/items", response_model=List[LaundryItemResponse])
async def get_laundry_items(
    vendor_id: str,
    category: Optional[str] = Query(None),
    is_available: Optional[bool] = Query(True),
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Get all laundry items for a vendor"""
    supabase = get_supabase_client()
    
    try:
        query = supabase.table("laundry_items").select("*").eq("laundry_vendor_id", vendor_id)
        
        if category:
            query = query.eq("category", category)
        if is_available is not None:
            query = query.eq("is_available", is_available)
            
        response = query.execute()
        
        return [LaundryItemResponse(**item) for item in response.data]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch laundry items: {str(e)}"
        )

@router.put("/vendors/{vendor_id}/items/{item_id}", response_model=LaundryItemResponse)
async def update_laundry_item(
    vendor_id: str,
    item_id: str,
    item_data: LaundryItemUpdate,
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Update a laundry item"""
    supabase = get_supabase_client()
    
    # Verify vendor ownership
    if current_user.role not in ["master"]:
        vendor_check = supabase.table("laundry_vendors").select("vendor_id").eq("id", vendor_id).execute()
        if not vendor_check.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
        
        user_vendor_check = supabase.table("vendors").select("user_id").eq("id", vendor_check.data[0]["vendor_id"]).execute()
        if not user_vendor_check.data or user_vendor_check.data[0]["user_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    try:
        update_data = {}
        for field, value in item_data.dict(exclude_unset=True).items():
            if field == "price_per_piece" and value is not None:
                update_data[field] = float(value)
            else:
                update_data[field] = value
        
        response = supabase.table("laundry_items").update(update_data).eq("id", item_id).eq("laundry_vendor_id", vendor_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Laundry item not found"
            )
        
        return LaundryItemResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update laundry item: {str(e)}"
        )

@router.delete("/vendors/{vendor_id}/items/{item_id}")
async def delete_laundry_item(
    vendor_id: str,
    item_id: str,
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Delete a laundry item"""
    supabase = get_supabase_client()
    
    # Verify vendor ownership
    if current_user.role not in ["master"]:
        vendor_check = supabase.table("laundry_vendors").select("vendor_id").eq("id", vendor_id).execute()
        if not vendor_check.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
        
        user_vendor_check = supabase.table("vendors").select("user_id").eq("id", vendor_check.data[0]["vendor_id"]).execute()
        if not user_vendor_check.data or user_vendor_check.data[0]["user_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    try:
        response = supabase.table("laundry_items").delete().eq("id", item_id).eq("laundry_vendor_id", vendor_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Laundry item not found"
            )
        
        return {"message": "Laundry item deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete laundry item: {str(e)}"
        )

# Laundry Orders Management Endpoints

@router.post("/orders", response_model=LaundryOrderResponse)
async def create_laundry_order(
    order_data: LaundryOrderCreate,
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Create a new laundry order"""
    if current_user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can create laundry orders"
        )
    
    supabase = get_supabase_client()
    
    try:
        # Generate order number
        order_number_response = supabase.rpc("generate_laundry_order_number").execute()
        order_number = order_number_response.data if order_number_response.data else f"LND-{datetime.now().strftime('%Y%m%d')}-001"
        
        # Calculate totals
        subtotal = Decimal('0.00')
        items_data = []
        
        for item in order_data.items:
            # Get item details and price
            item_response = supabase.table("laundry_items").select("*").eq("id", item.laundry_item_id).execute()
            if not item_response.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item {item.laundry_item_id} not found"
                )
            
            item_detail = item_response.data[0]
            unit_price = Decimal(str(item_detail["price_per_piece"]))
            total_price = unit_price * item.quantity
            subtotal += total_price
            
            items_data.append({
                "laundry_item_id": item.laundry_item_id,
                "quantity": item.quantity,
                "unit_price": float(unit_price),
                "total_price": float(total_price),
                "special_instructions": item.special_instructions
            })
        
        # Get vendor charges
        vendor_response = supabase.table("laundry_vendors").select("pickup_charge, delivery_charge").eq("id", order_data.laundry_vendor_id).execute()
        if not vendor_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Laundry vendor not found"
            )
        
        vendor = vendor_response.data[0]
        pickup_charge = Decimal(str(vendor["pickup_charge"]))
        delivery_charge = Decimal(str(vendor["delivery_charge"]))
        tax_amount = (subtotal + pickup_charge + delivery_charge) * Decimal('0.18')  # 18% GST
        total_amount = subtotal + pickup_charge + delivery_charge + tax_amount
        
        # Create order
        order_insert_data = {
            "user_id": current_user.id,
            "laundry_vendor_id": order_data.laundry_vendor_id,
            "order_number": order_number,
            "pickup_address": order_data.pickup_address,
            "pickup_date": order_data.pickup_date.isoformat(),
            "pickup_time_slot": order_data.pickup_time_slot,
            "pickup_instructions": order_data.pickup_instructions,
            "delivery_address": order_data.delivery_address or order_data.pickup_address,
            "delivery_instructions": order_data.delivery_instructions,
            "subtotal": float(subtotal),
            "pickup_charge": float(pickup_charge),
            "delivery_charge": float(delivery_charge),
            "tax_amount": float(tax_amount),
            "total_amount": float(total_amount)
        }
        
        order_response = supabase.table("laundry_orders").insert(order_insert_data).execute()
        
        if not order_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create laundry order"
            )
        
        created_order = order_response.data[0]
        
        # Create order items
        for item_data in items_data:
            item_data["laundry_order_id"] = created_order["id"]
            supabase.table("laundry_order_items").insert(item_data).execute()
        
        # Return complete order with items
        return await get_laundry_order(created_order["id"], current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create laundry order: {str(e)}"
        )

@router.get("/orders", response_model=List[LaundryOrderResponse])
async def get_laundry_orders(
    status: Optional[str] = Query(None),
    vendor_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Get laundry orders (filtered by user role)"""
    supabase = get_supabase_client()
    
    try:
        query = supabase.table("laundry_orders").select("""
            *,
            laundry_vendors!inner(business_name),
            users!inner(first_name, last_name, phone)
        """)
        
        if current_user.role == "user":
            query = query.eq("user_id", current_user.id)
        elif current_user.role == "vendor" and vendor_id:
            query = query.eq("laundry_vendor_id", vendor_id)
        elif current_user.role not in ["master"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if status:
            query = query.eq("status", status)
            
        response = query.execute()
        
        orders = []
        for order in response.data:
            # Get order items
            items_response = supabase.table("laundry_order_items").select("""
                *,
                laundry_items!inner(name, category, description)
            """).eq("laundry_order_id", order["id"]).execute()
            
            items = []
            for item in items_response.data:
                items.append({
                    "id": item["id"],
                    "laundry_item_id": item["laundry_item_id"],
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"],
                    "total_price": item["total_price"],
                    "special_instructions": item["special_instructions"],
                    "item_name": item["laundry_items"]["name"],
                    "item_category": item["laundry_items"]["category"],
                    "item_description": item["laundry_items"]["description"]
                })
            
            order_response = {
                **order,
                "items": items,
                "vendor_business_name": order["laundry_vendors"]["business_name"],
                "user_name": f"{order['users']['first_name']} {order['users']['last_name']}",
                "user_phone": order["users"]["phone"]
            }
            orders.append(LaundryOrderResponse(**order_response))
        
        return orders
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch laundry orders: {str(e)}"
        )

@router.get("/orders/{order_id}", response_model=LaundryOrderResponse)
async def get_laundry_order(
    order_id: str,
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Get a specific laundry order by ID"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("laundry_orders").select("""
            *,
            laundry_vendors!inner(business_name),
            users!inner(first_name, last_name, phone)
        """).eq("id", order_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Laundry order not found"
            )
        
        order = response.data[0]
        
        # Check access permissions
        if current_user.role == "user" and order["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get order items
        items_response = supabase.table("laundry_order_items").select("""
            *,
            laundry_items!inner(name, category, description)
        """).eq("laundry_order_id", order_id).execute()
        
        items = []
        for item in items_response.data:
            items.append({
                "id": item["id"],
                "laundry_item_id": item["laundry_item_id"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "total_price": item["total_price"],
                "special_instructions": item["special_instructions"],
                "item_name": item["laundry_items"]["name"],
                "item_category": item["laundry_items"]["category"],
                "item_description": item["laundry_items"]["description"]
            })
        
        order_response = {
            **order,
            "items": items,
            "vendor_business_name": order["laundry_vendors"]["business_name"],
            "user_name": f"{order['users']['first_name']} {order['users']['last_name']}",
            "user_phone": order["users"]["phone"]
        }
        
        return LaundryOrderResponse(**order_response)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch laundry order: {str(e)}"
        )

@router.put("/orders/{order_id}", response_model=LaundryOrderResponse)
async def update_laundry_order(
    order_id: str,
    order_data: LaundryOrderUpdate,
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Update a laundry order (mainly status updates by vendors)"""
    supabase = get_supabase_client()
    
    try:
        # Get current order
        order_response = supabase.table("laundry_orders").select("*").eq("id", order_id).execute()
        if not order_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Laundry order not found"
            )
        
        current_order = order_response.data[0]
        
        # Permission check
        if current_user.role == "user" and current_order["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        update_data = {}
        for field, value in order_data.dict(exclude_unset=True).items():
            if field == "pickup_date" and value:
                update_data[field] = value.isoformat()
            else:
                update_data[field] = value
        
        # Add timestamp for status changes
        if "status" in update_data:
            now = datetime.now().isoformat()
            if update_data["status"] == "confirmed":
                update_data["confirmed_at"] = now
            elif update_data["status"] == "picked_up":
                update_data["picked_up_at"] = now
            elif update_data["status"] == "ready":
                update_data["ready_at"] = now
            elif update_data["status"] == "delivered":
                update_data["delivered_at"] = now
            elif update_data["status"] == "cancelled":
                update_data["cancelled_at"] = now
        
        response = supabase.table("laundry_orders").update(update_data).eq("id", order_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Laundry order not found"
            )
        
        return await get_laundry_order(order_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update laundry order: {str(e)}"
        )

# Payment Endpoints

@router.post("/orders/{order_id}/payment", response_model=LaundryPaymentResponse)
async def process_laundry_payment(
    order_id: str,
    payment_data: LaundryPaymentRequest,
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Process payment for a laundry order (dummy implementation)"""
    supabase = get_supabase_client()
    
    try:
        # Get order
        order_response = supabase.table("laundry_orders").select("*").eq("id", order_id).execute()
        if not order_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Laundry order not found"
            )
        
        order = order_response.data[0]
        
        # Check permission
        if current_user.role == "user" and order["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Dummy payment processing
        payment_reference = f"PAY-LND-{datetime.now().strftime('%Y%m%d%H%M%S')}-{order_id[:8].upper()}"
        
        # Update order payment status
        update_data = {
            "payment_status": "paid",
            "payment_method": payment_data.payment_method,
            "payment_reference": payment_reference
        }
        
        supabase.table("laundry_orders").update(update_data).eq("id", order_id).execute()
        
        return LaundryPaymentResponse(
            success=True,
            payment_reference=payment_reference,
            message="Payment processed successfully (dummy implementation)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process payment: {str(e)}"
        )

# Dashboard Endpoints

@router.get("/vendors/{vendor_id}/dashboard", response_model=LaundryVendorDashboard)
async def get_vendor_dashboard(
    vendor_id: str,
    current_user: UserResponse = Depends(get_current_user_or_testing)
):
    """Get dashboard data for a laundry vendor"""
    supabase = get_supabase_client()
    
    # Verify vendor ownership
    if current_user.role not in ["master"]:
        vendor_check = supabase.table("laundry_vendors").select("vendor_id").eq("id", vendor_id).execute()
        if not vendor_check.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
        
        user_vendor_check = supabase.table("vendors").select("user_id").eq("id", vendor_check.data[0]["vendor_id"]).execute()
        if not user_vendor_check.data or user_vendor_check.data[0]["user_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    try:
        # Get order statistics
        orders_response = supabase.table("laundry_orders").select("status, total_amount, created_at").eq("laundry_vendor_id", vendor_id).execute()
        
        total_orders = len(orders_response.data)
        pending_orders = len([o for o in orders_response.data if o["status"] == "pending"])
        confirmed_orders = len([o for o in orders_response.data if o["status"] == "confirmed"])
        in_process_orders = len([o for o in orders_response.data if o["status"] == "in_process"])
        ready_orders = len([o for o in orders_response.data if o["status"] == "ready"])
        delivered_orders = len([o for o in orders_response.data if o["status"] == "delivered"])
        cancelled_orders = len([o for o in orders_response.data if o["status"] == "cancelled"])
        
        # Calculate revenue
        today = datetime.now().date()
        today_revenue = sum(
            Decimal(str(o["total_amount"])) for o in orders_response.data 
            if o["status"] == "delivered" and datetime.fromisoformat(o["created_at"].replace('Z', '+00:00')).date() == today
        )
        
        this_month = today.replace(day=1)
        monthly_revenue = sum(
            Decimal(str(o["total_amount"])) for o in orders_response.data 
            if o["status"] == "delivered" and datetime.fromisoformat(o["created_at"].replace('Z', '+00:00')).date() >= this_month
        )
        
        # Get active items count
        items_response = supabase.table("laundry_items").select("id").eq("laundry_vendor_id", vendor_id).eq("is_available", True).execute()
        active_items = len(items_response.data)
        
        # Get recent orders
        recent_orders_response = supabase.table("laundry_orders").select("""
            *,
            users!inner(first_name, last_name, phone)
        """).eq("laundry_vendor_id", vendor_id).order("created_at", desc=True).limit(5).execute()
        
        recent_orders = []
        for order in recent_orders_response.data:
            recent_orders.append({
                **order,
                "items": [],  # Simplified for dashboard
                "vendor_business_name": "",
                "user_name": f"{order['users']['first_name']} {order['users']['last_name']}",
                "user_phone": order["users"]["phone"]
            })
        
        stats = LaundryVendorStats(
            total_orders=total_orders,
            pending_orders=pending_orders,
            confirmed_orders=confirmed_orders,
            in_process_orders=in_process_orders,
            ready_orders=ready_orders,
            delivered_orders=delivered_orders,
            cancelled_orders=cancelled_orders,
            today_revenue=float(today_revenue),
            monthly_revenue=float(monthly_revenue),
            active_items=active_items
        )
        
        return LaundryVendorDashboard(
            stats=stats,
            recent_orders=[LaundryOrderResponse(**order) for order in recent_orders]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get vendor dashboard: {str(e)}"
        )

@router.get("/users/dashboard", response_model=LaundryUserStats)
async def get_user_dashboard(current_user: UserResponse = Depends(get_current_user)):
    """Get dashboard data for a user"""
    if current_user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can access user dashboard"
        )
    
    supabase = get_supabase_client()
    
    try:
        # Get user orders
        orders_response = supabase.table("laundry_orders").select("""
            *,
            laundry_vendors!inner(business_name)
        """).eq("user_id", current_user.id).execute()
        
        total_orders = len(orders_response.data)
        pending_orders = len([o for o in orders_response.data if o["status"] in ["pending", "confirmed", "picked_up", "in_process"]])
        delivered_orders = len([o for o in orders_response.data if o["status"] == "delivered"])
        total_spent = sum(Decimal(str(o["total_amount"])) for o in orders_response.data if o["status"] == "delivered")
        
        # Find favorite vendor
        vendor_counts = {}
        for order in orders_response.data:
            vendor_name = order["laundry_vendors"]["business_name"]
            vendor_counts[vendor_name] = vendor_counts.get(vendor_name, 0) + 1
        
        favorite_vendor = max(vendor_counts.items(), key=lambda x: x[1])[0] if vendor_counts else None
        
        # Get recent orders
        recent_orders = sorted(orders_response.data, key=lambda x: x["created_at"], reverse=True)[:5]
        recent_orders_formatted = []
        
        for order in recent_orders:
            recent_orders_formatted.append({
                **order,
                "items": [],  # Simplified for dashboard
                "vendor_business_name": order["laundry_vendors"]["business_name"],
                "user_name": f"{current_user.first_name} {current_user.last_name}",
                "user_phone": current_user.phone
            })
        
        return LaundryUserStats(
            total_orders=total_orders,
            pending_orders=pending_orders,
            delivered_orders=delivered_orders,
            total_spent=total_spent,
            favorite_vendor=favorite_vendor,
            recent_orders=[LaundryOrderResponse(**order) for order in recent_orders_formatted]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get user dashboard: {str(e)}"
        )
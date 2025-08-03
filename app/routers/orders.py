from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models import OrderCreate, OrderResponse, UserResponse, OrderStatus
from app.auth import get_current_user, require_role
from app.database import get_supabase_client

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    order_data = {
        "user_id": current_user.id,
        "vendor_id": order.vendor_id,
        "partner_id": order.partner_id,
        "total_amount": order.total_amount,
        "delivery_address": order.delivery_address,
        "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
        "delivery_time": order.delivery_time.isoformat() if order.delivery_time else None,
        "special_instructions": order.special_instructions,
        "status": OrderStatus.PENDING.value
    }
    
    try:
        # Create order
        order_response = supabase.table("orders").insert(order_data).execute()
        if not order_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create order"
            )
        
        created_order = order_response.data[0]
        order_id = created_order["id"]
        
        # Create order items
        for item in order.items:
            item_data = {
                "order_id": order_id,
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "total_price": item["quantity"] * item["unit_price"]
            }
            supabase.table("order_items").insert(item_data).execute()
        
        return OrderResponse(
            id=created_order["id"],
            user_id=created_order["user_id"],
            vendor_id=created_order["vendor_id"],
            partner_id=created_order.get("partner_id"),
            total_amount=created_order["total_amount"],
            status=created_order["status"],
            delivery_address=created_order.get("delivery_address"),
            delivery_date=created_order.get("delivery_date"),
            delivery_time=created_order.get("delivery_time"),
            special_instructions=created_order.get("special_instructions"),
            created_at=created_order["created_at"],
            updated_at=created_order["updated_at"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create order: {str(e)}"
        )

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    current_user: UserResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    # Users see their own orders, admins see orders for their vendor
    if current_user.role == "user":
        response = supabase.table("orders").select("*").eq("user_id", current_user.id).execute()
    elif current_user.role in ["admin", "partner"]:
        # Get vendor for admin/partner
        vendor_response = supabase.table("vendors").select("*").eq("admin_id", current_user.id).execute()
        if vendor_response.data:
            vendor_id = vendor_response.data[0]["id"]
            response = supabase.table("orders").select("*").eq("vendor_id", vendor_id).execute()
        else:
            response = supabase.table("orders").select("*").eq("partner_id", current_user.id).execute()
    else:
        # Master sees all orders
        response = supabase.table("orders").select("*").execute()
    
    orders = []
    for order_data in response.data:
        orders.append(OrderResponse(
            id=order_data["id"],
            user_id=order_data["user_id"],
            vendor_id=order_data["vendor_id"],
            partner_id=order_data.get("partner_id"),
            total_amount=order_data["total_amount"],
            status=order_data["status"],
            delivery_address=order_data.get("delivery_address"),
            delivery_date=order_data.get("delivery_date"),
            delivery_time=order_data.get("delivery_time"),
            special_instructions=order_data.get("special_instructions"),
            created_at=order_data["created_at"],
            updated_at=order_data["updated_at"]
        ))
    
    return orders

@router.put("/{order_id}/status")
async def update_order_status(
    order_id: str,
    new_status: OrderStatus,
    current_user: UserResponse = Depends(require_role(["admin", "partner", "master"]))
):
    supabase = get_supabase_client()
    
    try:
        # Update order status
        response = supabase.table("orders").update({
            "status": new_status.value
        }).eq("id", order_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Log status change
        supabase.table("order_status_history").insert({
            "order_id": order_id,
            "status": new_status.value,
            "changed_by": current_user.id
        }).execute()
        
        return {"message": "Order status updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update order status: {str(e)}"
        )

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    response = supabase.table("orders").select("*").eq("id", order_id).execute()
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order_data = response.data[0]
    
    # Check access permissions
    if (current_user.role == "user" and order_data["user_id"] != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    
    return OrderResponse(
        id=order_data["id"],
        user_id=order_data["user_id"],
        vendor_id=order_data["vendor_id"],
        partner_id=order_data.get("partner_id"),
        total_amount=order_data["total_amount"],
        status=order_data["status"],
        delivery_address=order_data.get("delivery_address"),
        delivery_date=order_data.get("delivery_date"),
        delivery_time=order_data.get("delivery_time"),
        special_instructions=order_data.get("special_instructions"),
        created_at=order_data["created_at"],
        updated_at=order_data["updated_at"]
    )
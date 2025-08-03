from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models import PaymentCreate, PaymentResponse, UserResponse, PaymentStatus
from app.auth import get_current_user
from app.database import get_supabase_client
import uuid

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/", response_model=PaymentResponse)
async def create_payment(
    payment: PaymentCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    # Verify order exists and belongs to user
    order_response = supabase.table("orders").select("*").eq("id", payment.order_id).execute()
    if not order_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order = order_response.data[0]
    if order["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create payment for this order"
        )
    
    # Generate mock transaction ID
    transaction_id = f"TX_{uuid.uuid4().hex[:8].upper()}"
    
    payment_data = {
        "order_id": payment.order_id,
        "user_id": current_user.id,
        "amount": payment.amount,
        "payment_method": payment.payment_method or "mock_payment",
        "status": PaymentStatus.PENDING.value,
        "transaction_id": transaction_id
    }
    
    try:
        response = supabase.table("payments").insert(payment_data).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create payment"
            )
        
        created_payment = response.data[0]
        
        # Mock payment processing - automatically mark as paid for demo
        supabase.table("payments").update({
            "status": PaymentStatus.PAID.value
        }).eq("id", created_payment["id"]).execute()
        
        # Update order status to confirmed
        supabase.table("orders").update({
            "status": "confirmed"
        }).eq("id", payment.order_id).execute()
        
        return PaymentResponse(
            id=created_payment["id"],
            order_id=created_payment["order_id"],
            user_id=created_payment["user_id"],
            amount=created_payment["amount"],
            payment_method=created_payment.get("payment_method"),
            status=PaymentStatus.PAID.value,  # Mock as paid
            transaction_id=created_payment.get("transaction_id"),
            created_at=created_payment["created_at"],
            updated_at=created_payment["updated_at"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create payment: {str(e)}"
        )

@router.get("/", response_model=List[PaymentResponse])
async def get_payments(
    current_user: UserResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    # Users see their own payments, admins see payments for their vendor orders
    if current_user.role == "user":
        response = supabase.table("payments").select("*").eq("user_id", current_user.id).execute()
    else:
        # For admins/masters, get all payments (could be filtered by vendor/community)
        response = supabase.table("payments").select("*").execute()
    
    payments = []
    for payment_data in response.data:
        payments.append(PaymentResponse(
            id=payment_data["id"],
            order_id=payment_data["order_id"],
            user_id=payment_data["user_id"],
            amount=payment_data["amount"],
            payment_method=payment_data.get("payment_method"),
            status=payment_data["status"],
            transaction_id=payment_data.get("transaction_id"),
            created_at=payment_data["created_at"],
            updated_at=payment_data["updated_at"]
        ))
    
    return payments

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    response = supabase.table("payments").select("*").eq("id", payment_id).execute()
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    payment_data = response.data[0]
    
    # Check access permissions
    if (current_user.role == "user" and payment_data["user_id"] != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this payment"
        )
    
    return PaymentResponse(
        id=payment_data["id"],
        order_id=payment_data["order_id"],
        user_id=payment_data["user_id"],
        amount=payment_data["amount"],
        payment_method=payment_data.get("payment_method"),
        status=payment_data["status"],
        transaction_id=payment_data.get("transaction_id"),
        created_at=payment_data["created_at"],
        updated_at=payment_data["updated_at"]
    )

@router.post("/{payment_id}/refund")
async def refund_payment(
    payment_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    # Check if payment exists
    payment_response = supabase.table("payments").select("*").eq("id", payment_id).execute()
    if not payment_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    payment = payment_response.data[0]
    
    if payment["status"] != PaymentStatus.PAID.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only refund paid payments"
        )
    
    try:
        # Update payment status to refunded
        supabase.table("payments").update({
            "status": PaymentStatus.REFUNDED.value
        }).eq("id", payment_id).execute()
        
        # Update related order status to cancelled
        supabase.table("orders").update({
            "status": "cancelled"
        }).eq("id", payment["order_id"]).execute()
        
        return {"message": "Payment refunded successfully", "transaction_id": payment["transaction_id"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to refund payment: {str(e)}"
        )
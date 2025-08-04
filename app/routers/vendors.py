from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models import VendorCreate, VendorResponse, UserResponse
from app.auth import get_current_user, require_role, get_password_hash
from app.database import get_supabase_client

router = APIRouter(prefix="/vendors", tags=["vendors"])

@router.post("/", response_model=VendorResponse)
async def create_vendor(
    vendor: VendorCreate,
    current_user: UserResponse = Depends(require_role(["master"]))
):
    supabase = get_supabase_client()
    
    try:
        # First, create a user account for the vendor with default credentials
        vendor_email = f"{vendor.name.lower().replace(' ', '_')}@vendor.test"
        hashed_password = get_password_hash("test")
        
        # Check if email already exists
        existing_user = supabase.table("users").select("*").eq("email", vendor_email).execute()
        if existing_user.data:
            # Generate a unique email by appending vendor type
            vendor_email = f"{vendor.name.lower().replace(' ', '_')}_{vendor.type.value}@vendor.test"
            existing_user = supabase.table("users").select("*").eq("email", vendor_email).execute()
            if existing_user.data:
                # Add timestamp to make it unique
                import time
                vendor_email = f"{vendor.name.lower().replace(' ', '_')}_{int(time.time())}@vendor.test"
        
        # Create user account for vendor
        user_data = {
            "email": vendor_email,
            "password_hash": hashed_password,
            "first_name": vendor.name.split()[0],
            "last_name": vendor.name.split()[-1] if len(vendor.name.split()) > 1 else "Vendor",
            "role": "vendor",
            "community_id": vendor.community_id,
            "is_active": True
        }
        
        user_response = supabase.table("users").insert(user_data).execute()
        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create vendor user account"
            )
        
        created_user = user_response.data[0]
        
        # Now create the vendor record
        vendor_data = {
            "name": vendor.name,
            "type": vendor.type.value,
            "community_id": vendor.community_id,
            "admin_id": vendor.admin_id,
            "description": vendor.description,
            "operating_hours": vendor.operating_hours,
            "user_id": created_user["id"],  # Link to the created user
            "email": vendor_email,
            "phone": f"+91-{vendor.name.replace(' ', '')[:8]}12345"  # Dummy phone
        }
        
        response = supabase.table("vendors").insert(vendor_data).execute()
        if not response.data:
            # If vendor creation fails, clean up the user account
            supabase.table("users").delete().eq("id", created_user["id"]).execute()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create vendor"
            )
        
        created_vendor = response.data[0]
        
        # If vendor type is laundry, create a laundry vendor profile
        if vendor.type.value == "laundry":
            laundry_vendor_data = {
                "vendor_id": created_vendor["id"],
                "business_name": vendor.name,
                "description": vendor.description or f"Professional laundry services by {vendor.name}",
                "pickup_time_start": "08:00:00",
                "pickup_time_end": "18:00:00",
                "delivery_time_hours": 24,
                "minimum_order_amount": 100.00,
                "pickup_charge": 20.00,
                "delivery_charge": 30.00,
                "service_areas": []
            }
            
            supabase.table("laundry_vendors").insert(laundry_vendor_data).execute()
            # Note: No default items are created - vendors need to add their own items
        
        return VendorResponse(
            id=created_vendor["id"],
            name=created_vendor["name"],
            type=created_vendor["type"],
            community_id=created_vendor["community_id"],
            admin_id=created_vendor.get("admin_id"),
            description=created_vendor.get("description"),
            operating_hours=created_vendor.get("operating_hours"),
            is_active=created_vendor["is_active"],
            created_at=created_vendor["created_at"],
            updated_at=created_vendor["updated_at"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create vendor: {str(e)}"
        )

@router.get("/", response_model=List[VendorResponse])
async def get_vendors(
    current_user: UserResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    # Filter vendors based on user role and community
    if current_user.role == "master":
        response = supabase.table("vendors").select("*").execute()
    else:
        if not current_user.community_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not associated with any community"
            )
        response = supabase.table("vendors").select("*").eq("community_id", current_user.community_id).execute()
    
    vendors = []
    for vendor_data in response.data:
        vendors.append(VendorResponse(
            id=vendor_data["id"],
            name=vendor_data["name"],
            type=vendor_data["type"],
            community_id=vendor_data["community_id"],
            admin_id=vendor_data.get("admin_id"),
            description=vendor_data.get("description"),
            operating_hours=vendor_data.get("operating_hours"),
            is_active=vendor_data["is_active"],
            created_at=vendor_data["created_at"],
            updated_at=vendor_data["updated_at"]
        ))
    
    return vendors

@router.get("/stats")
async def get_vendor_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get vendor statistics"""
    supabase = get_supabase_client()
    
    try:
        # Get vendors with basic stats
        vendors_response = supabase.table("vendors").select("*").execute()
        vendor_stats = []
        
        for vendor in vendors_response.data:
            # Get order count and revenue for this vendor
            orders_response = supabase.table("orders").select("*").eq("vendor_id", vendor["id"]).execute()
            
            total_orders = len(orders_response.data)
            total_revenue = sum([order.get("total_amount", 0) for order in orders_response.data if order.get("status") == "completed"])
            
            # Calculate average rating (placeholder - would need ratings table)
            rating = 4.5  # Default rating
            
            vendor_stats.append({
                "vendorId": vendor["id"],
                "vendorName": vendor["name"],
                "vendorType": vendor["type"],
                "orderCount": total_orders,
                "revenue": total_revenue,
                "rating": rating,
                "isActive": vendor["is_active"]
            })
        
        return vendor_stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch vendor stats: {str(e)}"
        )

@router.get("/search")
async def search_vendors(
    q: str = "",
    vendor_type: str = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Search vendors by name, with optional type filter"""
    supabase = get_supabase_client()
    
    try:
        # Build query based on search and filters
        query = supabase.table("vendors").select("*")
        
        if vendor_type:
            query = query.eq("type", vendor_type)
        
        # Supabase doesn't have ILIKE, so we'll filter in Python
        response = query.execute()
        
        vendors = []
        for vendor_data in response.data:
            # Filter by search term (if provided)
            if not q or (q.lower() in vendor_data["name"].lower() or 
                        q.lower() in vendor_data.get("description", "").lower()):
                
                # Get community name
                community_response = supabase.table("communities").select("name").eq("id", vendor_data["community_id"]).execute()
                community_name = community_response.data[0]["name"] if community_response.data else "Unknown"
                
                vendors.append({
                    "id": vendor_data["id"],
                    "name": vendor_data["name"],
                    "type": vendor_data["type"],
                    "email": vendor_data.get("email", ""),
                    "phone": vendor_data.get("phone", ""),
                    "address": vendor_data.get("address", ""),
                    "community_id": vendor_data["community_id"],
                    "community_name": community_name,
                    "description": vendor_data.get("description", ""),
                    "is_active": vendor_data["is_active"],
                    "created_at": vendor_data["created_at"],
                    "updated_at": vendor_data["updated_at"]
                })
        
        return vendors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search vendors: {str(e)}"
        )

@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    response = supabase.table("vendors").select("*").eq("id", vendor_id).execute()
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    vendor_data = response.data[0]
    
    # Check access permissions
    if (current_user.role != "master" and 
        current_user.community_id != vendor_data["community_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this vendor"
        )
    
    return VendorResponse(
        id=vendor_data["id"],
        name=vendor_data["name"],
        type=vendor_data["type"],
        community_id=vendor_data["community_id"],
        admin_id=vendor_data.get("admin_id"),
        description=vendor_data.get("description"),
        operating_hours=vendor_data.get("operating_hours"),
        is_active=vendor_data["is_active"],
        created_at=vendor_data["created_at"],
        updated_at=vendor_data["updated_at"]
    )

@router.put("/{vendor_id}")
async def update_vendor(
    vendor_id: str,
    vendor: VendorCreate,
    current_user: UserResponse = Depends(require_role(["master", "admin"]))
):
    supabase = get_supabase_client()
    
    # Check if user is admin of this vendor
    if current_user.role == "admin":
        vendor_check = supabase.table("vendors").select("*").eq("id", vendor_id).eq("admin_id", current_user.id).execute()
        if not vendor_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this vendor"
            )
    
    vendor_data = {
        "name": vendor.name,
        "type": vendor.type.value,
        "description": vendor.description,
        "operating_hours": vendor.operating_hours
    }
    
    try:
        response = supabase.table("vendors").update(vendor_data).eq("id", vendor_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        return {"message": "Vendor updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update vendor: {str(e)}"
        )

@router.patch("/{vendor_id}/status")
async def toggle_vendor_status(
    vendor_id: str,
    current_user: UserResponse = Depends(require_role(["master", "admin"]))
):
    """Toggle vendor active status"""
    supabase = get_supabase_client()
    
    # Get current vendor
    vendor_response = supabase.table("vendors").select("*").eq("id", vendor_id).execute()
    if not vendor_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    vendor = vendor_response.data[0]
    new_status = not vendor["is_active"]
    
    try:
        response = supabase.table("vendors").update({"is_active": new_status}).eq("id", vendor_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        updated_vendor = response.data[0]
        return VendorResponse(
            id=updated_vendor["id"],
            name=updated_vendor["name"],
            type=updated_vendor["type"],
            community_id=updated_vendor["community_id"],
            admin_id=updated_vendor.get("admin_id"),
            description=updated_vendor.get("description"),
            operating_hours=updated_vendor.get("operating_hours"),
            is_active=updated_vendor["is_active"],
            created_at=updated_vendor["created_at"],
            updated_at=updated_vendor["updated_at"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update vendor status: {str(e)}"
        )

@router.get("/community/{community_id}")
async def get_vendors_by_community(
    community_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all vendors in a specific community"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("vendors").select("*").eq("community_id", community_id).execute()
        
        vendors = []
        for vendor_data in response.data:
            # Get community name
            community_response = supabase.table("communities").select("name").eq("id", community_id).execute()
            community_name = community_response.data[0]["name"] if community_response.data else "Unknown"
            
            # Transform to match frontend interface
            vendors.append({
                "id": vendor_data["id"],
                "name": vendor_data["name"],
                "type": vendor_data["type"],
                "email": vendor_data.get("email", ""),
                "phone": vendor_data.get("phone", ""),
                "address": vendor_data.get("address", ""),
                "community_id": vendor_data["community_id"],
                "community_name": community_name,
                "description": vendor_data.get("description", ""),
                "is_active": vendor_data["is_active"],
                "rating": 4.5,  # Default rating
                "total_orders": 0,  # Would calculate from orders
                "monthly_revenue": 0,  # Would calculate from orders
                "created_at": vendor_data["created_at"],
                "updated_at": vendor_data["updated_at"],
                "last_active": vendor_data["updated_at"]
            })
        
        return vendors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch vendors by community: {str(e)}"
        )

@router.get("/type/{vendor_type}")
async def get_vendors_by_type(
    vendor_type: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all vendors of a specific type"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("vendors").select("*").eq("type", vendor_type).execute()
        
        vendors = []
        for vendor_data in response.data:
            # Get community name
            community_response = supabase.table("communities").select("name").eq("id", vendor_data["community_id"]).execute()
            community_name = community_response.data[0]["name"] if community_response.data else "Unknown"
            
            vendors.append({
                "id": vendor_data["id"],
                "name": vendor_data["name"],
                "type": vendor_data["type"],
                "email": vendor_data.get("email", ""),
                "phone": vendor_data.get("phone", ""),
                "address": vendor_data.get("address", ""),
                "community_id": vendor_data["community_id"],
                "community_name": community_name,
                "description": vendor_data.get("description", ""),
                "is_active": vendor_data["is_active"],
                "rating": 4.5,
                "total_orders": 0,
                "monthly_revenue": 0,
                "created_at": vendor_data["created_at"],
                "updated_at": vendor_data["updated_at"],
                "last_active": vendor_data["updated_at"]
            })
        
        return vendors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch vendors by type: {str(e)}"
        )
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models import VendorCreate, VendorResponse, UserResponse
from app.auth import get_current_user, require_role
from app.database import get_supabase_client

router = APIRouter(prefix="/vendors", tags=["vendors"])

@router.post("/", response_model=VendorResponse)
async def create_vendor(
    vendor: VendorCreate,
    current_user: UserResponse = Depends(require_role(["master"]))
):
    supabase = get_supabase_client()
    
    vendor_data = {
        "name": vendor.name,
        "type": vendor.type.value,
        "community_id": vendor.community_id,
        "admin_id": vendor.admin_id,
        "description": vendor.description,
        "operating_hours": vendor.operating_hours
    }
    
    try:
        response = supabase.table("vendors").insert(vendor_data).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create vendor"
            )
        
        created_vendor = response.data[0]
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
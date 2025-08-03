from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.database import get_supabase_client
from app.auth import get_current_user
from app.models import CommunityCreate, CommunityResponse, UserResponse
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/communities", tags=["communities"])

class CommunityUpdate(BaseModel):
    name: str
    address: str
    admin_name: str
    admin_email: str
    admin_phone: Optional[str] = None

class CommunityStats(BaseModel):
    communityId: str
    communityName: str
    vendorCount: int
    userCount: int
    orderCount: int
    revenue: float

class CommunityStatusUpdate(BaseModel):
    is_active: bool

@router.get("/", response_model=List[dict])
async def get_communities(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all communities"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("communities").select("*").order("created_at", desc=True).execute()
        
        communities = []
        for row in response.data:
            communities.append({
                "id": str(row["id"]),
                "name": row["name"],
                "address": row.get("address", ""),
                "community_code": row["code"],
                "admin_name": row.get("admin_name", ""),
                "admin_email": row.get("admin_email", ""),
                "admin_phone": row.get("admin_phone", ""),
                "is_active": row.get("is_active", True),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        
        return communities
    except Exception as e:
        print(f"Error fetching communities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch communities")

@router.get("/stats", response_model=List[CommunityStats])
async def get_community_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get community statistics"""
    supabase = get_supabase_client()
    
    try:
        # Get all communities
        communities_response = supabase.table("communities").select("*").eq("is_active", True).execute()
        
        stats = []
        for community in communities_response.data:
            community_id = community["id"]
            
            # Get vendor count
            vendors_response = supabase.table("vendors").select("id").eq("community_id", community_id).eq("is_active", True).execute()
            vendor_count = len(vendors_response.data)
            
            # Get user count
            users_response = supabase.table("users").select("id").eq("community_id", community_id).eq("is_active", True).execute()
            user_count = len(users_response.data)
            
            # Get order count and revenue from vendors in this community
            order_count = 0
            revenue = 0
            
            if vendors_response.data:
                vendor_ids = [v["id"] for v in vendors_response.data]
                for vendor_id in vendor_ids:
                    orders_response = supabase.table("orders").select("*").eq("vendor_id", vendor_id).execute()
                    order_count += len(orders_response.data)
                    
                    for order in orders_response.data:
                        if order.get("status") == "completed":
                            revenue += order.get("total_amount", 0)
            
            stats.append({
                "communityId": str(community_id),
                "communityName": community["name"],
                "vendorCount": vendor_count,
                "userCount": user_count,
                "orderCount": order_count,
                "revenue": float(revenue)
            })
        
        # Sort by revenue descending
        stats.sort(key=lambda x: x["revenue"], reverse=True)
        return stats
    except Exception as e:
        print(f"Error fetching community stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch community statistics")

@router.get("/{community_id}")
async def get_community(
    community_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific community by ID"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("communities").select("*").eq("id", community_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Community not found")
        
        row = response.data[0]
        return {
            "id": str(row["id"]),
            "name": row["name"],
            "address": row.get("address", ""),
            "community_code": row["code"],
            "admin_name": row.get("admin_name", ""),
            "admin_email": row.get("admin_email", ""),
            "admin_phone": row.get("admin_phone", ""),
            "is_active": row.get("is_active", True),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching community: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch community")

@router.post("/")
async def create_community(
    community: CommunityUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new community"""
    supabase = get_supabase_client()
    
    try:
        # Generate a unique community code
        community_code = f"COM{str(uuid.uuid4())[:8].upper()}"
        
        community_data = {
            "name": community.name,
            "address": community.address,
            "code": community_code,
            "admin_name": community.admin_name,
            "admin_email": community.admin_email,
            "admin_phone": community.admin_phone,
            "is_active": True
        }
        
        response = supabase.table("communities").insert(community_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create community")
        
        created_community = response.data[0]
        return {
            "id": str(created_community["id"]),
            "name": created_community["name"],
            "address": created_community.get("address", ""),
            "community_code": created_community["code"],
            "admin_name": created_community.get("admin_name", ""),
            "admin_email": created_community.get("admin_email", ""),
            "admin_phone": created_community.get("admin_phone", ""),
            "is_active": created_community.get("is_active", True),
            "created_at": created_community["created_at"],
            "updated_at": created_community["updated_at"]
        }
    except Exception as e:
        print(f"Error creating community: {e}")
        raise HTTPException(status_code=500, detail="Failed to create community")

@router.put("/{community_id}")
async def update_community(
    community_id: str,
    community: CommunityUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update an existing community"""
    supabase = get_supabase_client()
    
    try:
        update_data = {
            "name": community.name,
            "address": community.address,
            "admin_name": community.admin_name,
            "admin_email": community.admin_email,
            "admin_phone": community.admin_phone
        }
        
        response = supabase.table("communities").update(update_data).eq("id", community_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Community not found")
        
        updated_community = response.data[0]
        return {
            "id": str(updated_community["id"]),
            "name": updated_community["name"],
            "address": updated_community.get("address", ""),
            "community_code": updated_community["code"],
            "admin_name": updated_community.get("admin_name", ""),
            "admin_email": updated_community.get("admin_email", ""),
            "admin_phone": updated_community.get("admin_phone", ""),
            "is_active": updated_community.get("is_active", True),
            "created_at": updated_community["created_at"],
            "updated_at": updated_community["updated_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating community: {e}")
        raise HTTPException(status_code=500, detail="Failed to update community")

@router.patch("/{community_id}/status")
async def toggle_community_status(
    community_id: str,
    status_update: CommunityStatusUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Toggle community active status"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("communities").update({
            "is_active": status_update.is_active
        }).eq("id", community_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Community not found")
        
        updated_community = response.data[0]
        return {
            "id": str(updated_community["id"]),
            "name": updated_community["name"],
            "address": updated_community.get("address", ""),
            "community_code": updated_community["code"],
            "admin_name": updated_community.get("admin_name", ""),
            "admin_email": updated_community.get("admin_email", ""),
            "admin_phone": updated_community.get("admin_phone", ""),
            "is_active": updated_community.get("is_active", True),
            "created_at": updated_community["created_at"],
            "updated_at": updated_community["updated_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error toggling community status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update community status")

@router.delete("/{community_id}")
async def delete_community(
    community_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a community"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("communities").delete().eq("id", community_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Community not found")
        
        return {"message": "Community deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting community: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete community")

@router.get("/search")
async def search_communities(
    q: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Search communities by name, code, or address"""
    supabase = get_supabase_client()
    
    try:
        # Supabase doesn't have ILIKE, so we'll get all and filter in Python
        response = supabase.table("communities").select("*").execute()
        
        communities = []
        search_term = q.lower()
        
        for row in response.data:
            if (search_term in row["name"].lower() or 
                search_term in row["code"].lower() or 
                search_term in row.get("address", "").lower()):
                
                communities.append({
                    "id": str(row["id"]),
                    "name": row["name"],
                    "address": row.get("address", ""),
                    "community_code": row["code"],
                    "admin_name": row.get("admin_name", ""),
                    "admin_email": row.get("admin_email", ""),
                    "admin_phone": row.get("admin_phone", ""),
                    "is_active": row.get("is_active", True),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                })
        
        return communities
    except Exception as e:
        print(f"Error searching communities: {e}")
        raise HTTPException(status_code=500, detail="Failed to search communities")
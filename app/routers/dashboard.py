from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime, timedelta
from app.database import get_supabase_client
from app.auth import get_current_user
from app.models import UserResponse
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

class DashboardStats(BaseModel):
    totalCommunities: int
    totalVendors: int
    totalUsers: int
    totalOrders: int
    totalRevenue: float
    activeUsers: int
    pendingOrders: int
    completedOrders: int

class OrderTrend(BaseModel):
    date: str
    orders: int
    revenue: float

class RecentActivity(BaseModel):
    id: str
    type: str
    message: str
    timestamp: str
    icon: str
    color: str

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get master dashboard statistics"""
    supabase = get_supabase_client()
    
    try:
        # Get communities count
        communities_response = supabase.table("communities").select("id").eq("is_active", True).execute()
        total_communities = len(communities_response.data)
        
        # Get vendors count
        vendors_response = supabase.table("vendors").select("id").eq("is_active", True).execute()
        total_vendors = len(vendors_response.data)
        
        # Get users count
        users_response = supabase.table("users").select("id, updated_at").eq("is_active", True).execute()
        total_users = len(users_response.data)
        
        # Calculate active users (updated in last 7 days)
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        active_users = len([u for u in users_response.data if u["updated_at"] > seven_days_ago])
        
        # Get orders
        orders_response = supabase.table("orders").select("id, status, total_amount").execute()
        total_orders = len(orders_response.data)
        
        # Calculate order stats and revenue
        pending_orders = len([o for o in orders_response.data if o["status"] == "pending"])
        completed_orders = len([o for o in orders_response.data if o["status"] == "completed"])
        total_revenue = sum([o.get("total_amount", 0) for o in orders_response.data if o["status"] == "completed"])
        
        return DashboardStats(
            totalCommunities=total_communities,
            totalVendors=total_vendors,
            totalUsers=total_users,
            totalOrders=total_orders,
            totalRevenue=float(total_revenue),
            activeUsers=active_users,
            pendingOrders=pending_orders,
            completedOrders=completed_orders
        )
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard statistics")

@router.get("/order-trends", response_model=List[OrderTrend])
async def get_order_trends(
    days: int = 7,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get order trends for the specified number of days"""
    supabase = get_supabase_client()
    
    try:
        # Get orders from the last N days
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        orders_response = supabase.table("orders").select("created_at, status, total_amount").gte("created_at", start_date).execute()
        
        # Group orders by date
        trends = {}
        
        # Initialize all days with 0
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-1-i)).strftime('%Y-%m-%d')
            trends[date] = {"orders": 0, "revenue": 0}
        
        # Populate with actual data
        for order in orders_response.data:
            order_date = datetime.fromisoformat(order["created_at"].replace('Z', '+00:00')).strftime('%Y-%m-%d')
            if order_date in trends:
                trends[order_date]["orders"] += 1
                if order["status"] == "completed":
                    trends[order_date]["revenue"] += order.get("total_amount", 0)
        
        # Convert to list format
        result = []
        for date in sorted(trends.keys()):
            result.append(OrderTrend(
                date=date,
                orders=trends[date]["orders"],
                revenue=float(trends[date]["revenue"])
            ))
        
        return result
    except Exception as e:
        print(f"Error fetching order trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch order trends")

@router.get("/recent-activities", response_model=List[RecentActivity])
async def get_recent_activities(
    limit: int = 10,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get recent platform activities"""
    supabase = get_supabase_client()
    
    try:
        activities = []
        
        # Get recent user registrations (last 7 days)
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        users_response = supabase.table("users").select("id, first_name, last_name, created_at, community_id").gte("created_at", seven_days_ago).order("created_at", desc=True).limit(3).execute()
        
        for user in users_response.data:
            # Get community name
            community_name = "Unknown Community"
            if user.get("community_id"):
                community_response = supabase.table("communities").select("name").eq("id", user["community_id"]).execute()
                if community_response.data:
                    community_name = community_response.data[0]["name"]
            
            activities.append(RecentActivity(
                id=str(user["id"]),
                type="new_user",
                message=f"New user {user['first_name']} {user['last_name']} registered in {community_name}",
                timestamp=user["created_at"],
                icon="person-add",
                color="#22c55e"
            ))
        
        # Get recent orders (last 24 hours)
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        
        orders_response = supabase.table("orders").select("id, created_at, vendor_id").gte("created_at", yesterday).order("created_at", desc=True).limit(3).execute()
        
        for order in orders_response.data:
            # Get vendor name
            vendor_name = "Unknown Vendor"
            vendor_response = supabase.table("vendors").select("name").eq("id", order["vendor_id"]).execute()
            if vendor_response.data:
                vendor_name = vendor_response.data[0]["name"]
            
            activities.append(RecentActivity(
                id=str(order["id"]),
                type="new_order",
                message=f"Order #{str(order['id'])[:8]} placed for {vendor_name}",
                timestamp=order["created_at"],
                icon="bag",
                color="#3b82f6"
            ))
        
        # Get recently activated vendors (last 24 hours)
        vendors_response = supabase.table("vendors").select("id, name, updated_at").eq("is_active", True).gte("updated_at", yesterday).order("updated_at", desc=True).limit(2).execute()
        
        for vendor in vendors_response.data:
            activities.append(RecentActivity(
                id=str(vendor["id"]),
                type="vendor_active",
                message=f"{vendor['name']} went online",
                timestamp=vendor["updated_at"],
                icon="checkmark-circle",
                color="#10b981"
            ))
        
        # Get recent payments (last 24 hours)
        payments_response = supabase.table("payments").select("id, amount, created_at").eq("status", "paid").gte("created_at", yesterday).order("created_at", desc=True).limit(2).execute()
        
        for payment in payments_response.data:
            activities.append(RecentActivity(
                id=str(payment["id"]),
                type="payment",
                message=f"Payment of ${payment['amount']} received",
                timestamp=payment["created_at"],
                icon="card",
                color="#f59e0b"
            ))
        
        # Sort by timestamp and limit
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        return activities[:limit]
        
    except Exception as e:
        print(f"Error fetching recent activities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent activities")

@router.get("/community-performance")
async def get_community_performance(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get community performance metrics"""
    supabase = get_supabase_client()
    
    try:
        communities_response = supabase.table("communities").select("*").eq("is_active", True).execute()
        
        performance = []
        for community in communities_response.data:
            community_id = community["id"]
            
            # Get user count
            users_response = supabase.table("users").select("id").eq("community_id", community_id).eq("is_active", True).execute()
            user_count = len(users_response.data)
            
            # Get vendor count
            vendors_response = supabase.table("vendors").select("id").eq("community_id", community_id).eq("is_active", True).execute()
            vendor_count = len(vendors_response.data)
            
            # Get order count and revenue
            order_count = 0
            revenue = 0
            
            if vendors_response.data:
                vendor_ids = [v["id"] for v in vendors_response.data]
                for vendor_id in vendor_ids:
                    orders_response = supabase.table("orders").select("total_amount, status").eq("vendor_id", vendor_id).execute()
                    order_count += len(orders_response.data)
                    
                    for order in orders_response.data:
                        if order.get("status") == "completed":
                            revenue += order.get("total_amount", 0)
            
            avg_order_value = revenue / order_count if order_count > 0 else 0
            
            performance.append({
                "id": str(community_id),
                "name": community["name"],
                "code": community["code"],
                "userCount": user_count,
                "vendorCount": vendor_count,
                "orderCount": order_count,
                "revenue": float(revenue),
                "avgOrderValue": float(avg_order_value)
            })
        
        # Sort by revenue descending
        performance.sort(key=lambda x: x["revenue"], reverse=True)
        return performance
    except Exception as e:
        print(f"Error fetching community performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch community performance")

@router.get("/vendor-performance")
async def get_vendor_performance(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get vendor performance metrics"""
    supabase = get_supabase_client()
    
    try:
        vendors_response = supabase.table("vendors").select("*").execute()
        
        performance = []
        for vendor in vendors_response.data:
            vendor_id = vendor["id"]
            
            # Get community name
            community_name = "Unknown"
            community_response = supabase.table("communities").select("name").eq("id", vendor["community_id"]).execute()
            if community_response.data:
                community_name = community_response.data[0]["name"]
            
            # Get order stats
            orders_response = supabase.table("orders").select("total_amount, status").eq("vendor_id", vendor_id).execute()
            order_count = len(orders_response.data)
            
            revenue = sum([o.get("total_amount", 0) for o in orders_response.data if o.get("status") == "completed"])
            avg_order_value = revenue / order_count if order_count > 0 else 0
            
            performance.append({
                "id": str(vendor_id),
                "name": vendor["name"],
                "type": vendor["type"],
                "communityName": community_name,
                "isActive": vendor["is_active"],
                "orderCount": order_count,
                "revenue": float(revenue),
                "avgOrderValue": float(avg_order_value)
            })
        
        # Sort by revenue descending
        performance.sort(key=lambda x: x["revenue"], reverse=True)
        return performance
    except Exception as e:
        print(f"Error fetching vendor performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch vendor performance")
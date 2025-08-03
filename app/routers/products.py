from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models import ProductCreate, ProductResponse, UserResponse
from app.auth import get_current_user, require_role
from app.database import get_supabase_client

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    current_user: UserResponse = Depends(require_role(["admin", "master"]))
):
    supabase = get_supabase_client()
    
    # Check if user is admin of the vendor
    if current_user.role == "admin":
        vendor_check = supabase.table("vendors").select("*").eq("id", product.vendor_id).eq("admin_id", current_user.id).execute()
        if not vendor_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create products for this vendor"
            )
    
    product_data = {
        "vendor_id": product.vendor_id,
        "category_id": product.category_id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "unit": product.unit,
        "image_url": product.image_url
    }
    
    try:
        response = supabase.table("products").insert(product_data).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create product"
            )
        
        created_product = response.data[0]
        return ProductResponse(
            id=created_product["id"],
            vendor_id=created_product["vendor_id"],
            category_id=created_product.get("category_id"),
            name=created_product["name"],
            description=created_product.get("description"),
            price=created_product["price"],
            unit=created_product.get("unit"),
            image_url=created_product.get("image_url"),
            is_available=created_product["is_available"],
            created_at=created_product["created_at"],
            updated_at=created_product["updated_at"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create product: {str(e)}"
        )

@router.get("/vendor/{vendor_id}", response_model=List[ProductResponse])
async def get_products_by_vendor(
    vendor_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    response = supabase.table("products").select("*").eq("vendor_id", vendor_id).eq("is_available", True).execute()
    
    products = []
    for product_data in response.data:
        products.append(ProductResponse(
            id=product_data["id"],
            vendor_id=product_data["vendor_id"],
            category_id=product_data.get("category_id"),
            name=product_data["name"],
            description=product_data.get("description"),
            price=product_data["price"],
            unit=product_data.get("unit"),
            image_url=product_data.get("image_url"),
            is_available=product_data["is_available"],
            created_at=product_data["created_at"],
            updated_at=product_data["updated_at"]
        ))
    
    return products

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    response = supabase.table("products").select("*").eq("id", product_id).execute()
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product_data = response.data[0]
    
    return ProductResponse(
        id=product_data["id"],
        vendor_id=product_data["vendor_id"],
        category_id=product_data.get("category_id"),
        name=product_data["name"],
        description=product_data.get("description"),
        price=product_data["price"],
        unit=product_data.get("unit"),
        image_url=product_data.get("image_url"),
        is_available=product_data["is_available"],
        created_at=product_data["created_at"],
        updated_at=product_data["updated_at"]
    )

@router.put("/{product_id}")
async def update_product(
    product_id: str,
    product: ProductCreate,
    current_user: UserResponse = Depends(require_role(["admin", "master"]))
):
    supabase = get_supabase_client()
    
    # Check if user is admin of the vendor
    if current_user.role == "admin":
        vendor_check = supabase.table("vendors").select("*").eq("id", product.vendor_id).eq("admin_id", current_user.id).execute()
        if not vendor_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update products for this vendor"
            )
    
    product_data = {
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "unit": product.unit,
        "image_url": product.image_url
    }
    
    try:
        response = supabase.table("products").update(product_data).eq("id", product_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return {"message": "Product updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update product: {str(e)}"
        )

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user: UserResponse = Depends(require_role(["admin", "master"]))
):
    supabase = get_supabase_client()
    
    try:
        # Soft delete by setting is_available to False
        response = supabase.table("products").update({"is_available": False}).eq("id", product_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return {"message": "Product deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete product: {str(e)}"
        )
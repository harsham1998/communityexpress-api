from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from app.models import UserCreate, UserResponse, LoginRequest, Token
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user
from app.database import get_supabase_client
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    supabase = get_supabase_client()
    
    # Check if user already exists
    existing_user = supabase.table("users").select("*").eq("email", user.email).execute()
    if existing_user.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    
    user_data = {
        "email": user.email,
        "password_hash": hashed_password,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "role": user.role.value,
        "community_id": user.community_id,
        "apartment_number": user.apartment_number
    }
    
    try:
        response = supabase.table("users").insert(user_data).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
        
        created_user = response.data[0]
        return UserResponse(
            id=created_user["id"],
            email=created_user["email"],
            first_name=created_user["first_name"],
            last_name=created_user["last_name"],
            phone=created_user.get("phone"),
            role=created_user["role"],
            community_id=created_user.get("community_id"),
            apartment_number=created_user.get("apartment_number"),
            is_active=created_user["is_active"],
            created_at=created_user["created_at"],
            updated_at=created_user["updated_at"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    supabase = get_supabase_client()
    
    # Get user by email
    response = supabase.table("users").select("*").eq("email", login_data.email).execute()
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    user_data = response.data[0]
    
    # Verify password
    if not verify_password(login_data.password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data["id"]}, expires_delta=access_token_expires
    )
    
    user_response = UserResponse(
        id=user_data["id"],
        email=user_data["email"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        phone=user_data.get("phone"),
        role=user_data["role"],
        community_id=user_data.get("community_id"),
        apartment_number=user_data.get("apartment_number"),
        is_active=user_data["is_active"],
        created_at=user_data["created_at"],
        updated_at=user_data["updated_at"]
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@router.post("/join-community")
async def join_community(
    community_code: str,
    current_user: UserResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    # Get community by code
    community_response = supabase.table("communities").select("*").eq("code", community_code).execute()
    if not community_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid community code"
        )
    
    community = community_response.data[0]
    
    # Update user's community
    try:
        update_response = supabase.table("users").update({
            "community_id": community["id"]
        }).eq("id", current_user.id).execute()
        
        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to join community"
            )
        
        return {"message": "Successfully joined community", "community_name": community["name"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to join community: {str(e)}"
        )
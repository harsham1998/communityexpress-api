#!/usr/bin/env python3
"""
Script to create a master user with properly hashed password
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.auth import get_password_hash
from app.database import get_supabase_client

def create_master_user():
    supabase = get_supabase_client()
    
    # Hash the password
    password = "Master123!"
    hashed_password = get_password_hash(password)
    
    print(f"Hashed password: {hashed_password}")
    
    # Check if user exists
    existing_user = supabase.table("users").select("*").eq("email", "master@communityexpress.com").execute()
    
    if existing_user.data:
        # Update existing user with hashed password
        result = supabase.table("users").update({
            "password_hash": hashed_password,
            "role": "master"
        }).eq("email", "master@communityexpress.com").execute()
        
        print("Updated existing master user with hashed password")
        print(f"Result: {result}")
    else:
        # Create new user
        user_data = {
            "email": "master@communityexpress.com",
            "password_hash": hashed_password,
            "first_name": "Master",
            "last_name": "Admin",
            "role": "master",
            "is_active": True
        }
        
        result = supabase.table("users").insert(user_data).execute()
        print("Created new master user")
        print(f"Result: {result}")

if __name__ == "__main__":
    create_master_user()
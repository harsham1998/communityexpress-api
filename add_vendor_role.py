#!/usr/bin/env python3
"""
Migration script to add 'vendor' role to user_role enum in Supabase
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

def add_vendor_role():
    """Add 'vendor' to the user_role enum if it doesn't exist"""
    
    try:
        # First, let's check current enum values
        print("Checking current user_role enum values...")
        
        # Try to create a test user with vendor role to see if it works
        test_data = {
            "email": "test_vendor_role@test.com",
            "password_hash": "dummy_hash", 
            "first_name": "Test",
            "last_name": "Vendor",
            "role": "vendor",
            "is_active": False  # Make it inactive so it doesn't interfere
        }
        
        # Try inserting to see if vendor role is accepted
        response = supabase.table("users").insert(test_data).execute()
        
        if response.data:
            print("✅ 'vendor' role already exists in user_role enum")
            # Clean up test user
            supabase.table("users").delete().eq("email", "test_vendor_role@test.com").execute()
        else:
            print("❌ 'vendor' role does not exist in user_role enum")
            print("Need to add it manually via Supabase SQL Editor")
            
    except Exception as e:
        if "invalid input value for enum user_role" in str(e):
            print("❌ 'vendor' role does not exist in user_role enum")
            print("\nTo fix this, run the following SQL in your Supabase SQL Editor:")
            print("\nALTER TYPE user_role ADD VALUE 'vendor';")
            print("\nThis will add 'vendor' as a valid role option.")
        else:
            print(f"❌ Error checking enum: {e}")

if __name__ == "__main__":
    add_vendor_role()
#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Laundry System
This script tests all the newly created laundry APIs
"""

import requests
import json
import time
from datetime import datetime, date, timedelta

# API Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json", "X-Testing": "true"}

class LaundryAPITester:
    def __init__(self):
        self.access_token = None
        self.master_token = None
        self.vendor_token = None
        self.vendor_id = None
        self.laundry_vendor_id = None
        self.community_id = None
        self.created_items = []
        self.created_orders = []
        
    def login(self, email, password):
        """Login and get access token"""
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password},
            headers=HEADERS
        )
        if response.status_code == 200:
            data = response.json()
            return data["access_token"], data["user"]
        else:
            print(f"Login failed for {email}: {response.text}")
            return None, None
    
    def get_auth_headers(self, token=None):
        """Get headers with authorization or testing mode"""
        if token:
            return {**HEADERS, "Authorization": f"Bearer {token}"}
        else:
            # Return testing headers for localhost testing
            return HEADERS
    
    def test_master_login(self):
        """Test master login"""
        print("\n=== Testing Master Login ===")
        token, user = self.login("master@test.com", "master123")
        if token:
            self.master_token = token
            self.community_id = user.get("community_id")
            print(f"✓ Master login successful")
            print(f"  User: {user['first_name']} {user['last_name']}")
            print(f"  Role: {user['role']}")
            print(f"  Community ID: {self.community_id}")
            return True
        else:
            print("✗ Master login failed")
            return False
    
    def test_create_vendor(self):
        """Test creating a vendor with auto-generated login"""
        print("\n=== Testing Vendor Creation ===")
        if not self.master_token:
            print("✗ No master token available")
            return False
        
        vendor_data = {
            "name": "QuickWash Laundry",
            "type": "laundry",
            "community_id": self.community_id,
            "description": "Professional laundry services with pickup and delivery"
        }
        
        response = requests.post(
            f"{BASE_URL}/vendors/",
            json=vendor_data,
            headers=self.get_auth_headers(self.master_token)
        )
        
        if response.status_code == 200:
            vendor = response.json()
            self.vendor_id = vendor["id"]
            print(f"✓ Vendor created successfully")
            print(f"  Vendor ID: {self.vendor_id}")
            print(f"  Name: {vendor['name']}")
            print(f"  Type: {vendor['type']}")
            
            # Try to login with the auto-generated credentials
            vendor_email = f"{vendor_data['name'].lower().replace(' ', '_')}@vendor.test"
            print(f"  Generated Email: {vendor_email}")
            print(f"  Default Password: test")
            return True
        else:
            print(f"✗ Vendor creation failed: {response.text}")
            return False
    
    def test_vendor_login(self):
        """Test vendor login with auto-generated credentials"""
        print("\n=== Testing Vendor Login ===")
        vendor_email = "quickwash_laundry@vendor.test"
        token, user = self.login(vendor_email, "test")
        if token:
            self.vendor_token = token
            print(f"✓ Vendor login successful")
            print(f"  User: {user['first_name']} {user['last_name']}")
            print(f"  Role: {user['role']}")
            print(f"  Email: {user['email']}")
            return True
        else:
            print("✗ Vendor login failed")
            return False
    
    def test_get_laundry_vendors(self):
        """Test getting laundry vendors"""
        print("\n=== Testing Get Laundry Vendors ===")
        response = requests.get(
            f"{BASE_URL}/laundry/vendors",
            headers=self.get_auth_headers()  # Use testing headers for localhost
        )
        
        if response.status_code == 200:
            vendors = response.json()
            print(f"✓ Retrieved {len(vendors)} laundry vendors")
            if vendors:
                self.laundry_vendor_id = vendors[0]["id"]
                print(f"  First vendor ID: {self.laundry_vendor_id}")
                print(f"  Business name: {vendors[0]['business_name']}")
                print(f"  Pickup charge: ₹{vendors[0]['pickup_charge']}")
                print(f"  Delivery charge: ₹{vendors[0]['delivery_charge']}")
            return True
        else:
            print(f"✗ Failed to get laundry vendors: {response.text}")
            return False
    
    def test_get_laundry_items(self):
        """Test getting laundry items"""
        print("\n=== Testing Get Laundry Items ===")
        if not self.laundry_vendor_id:
            print("✗ No laundry vendor ID available")
            return False
        
        response = requests.get(
            f"{BASE_URL}/laundry/vendors/{self.laundry_vendor_id}/items",
            headers=self.get_auth_headers()  # Use testing headers for localhost
        )
        
        if response.status_code == 200:
            items = response.json()
            print(f"✓ Retrieved {len(items)} laundry items")
            for i, item in enumerate(items[:3]):  # Show first 3 items
                print(f"  {i+1}. {item['name']} - ₹{item['price_per_piece']} ({item['category']})")
                self.created_items.append(item["id"])
            return True
        else:
            print(f"✗ Failed to get laundry items: {response.text}")
            return False
    
    def test_create_laundry_item(self):
        """Test creating a new laundry item"""
        print("\n=== Testing Create Laundry Item ===")
        if not self.laundry_vendor_id or not self.vendor_token:
            print("✗ Missing laundry vendor ID or vendor token")
            return False
        
        item_data = {
            "name": "Premium Suit",
            "description": "High-end suit dry cleaning with special care",
            "category": "dry_clean",
            "price_per_piece": 200.00,
            "estimated_time_hours": 48
        }
        
        response = requests.post(
            f"{BASE_URL}/laundry/vendors/{self.laundry_vendor_id}/items",
            json=item_data,
            headers=self.get_auth_headers()  # Use testing headers for localhost
        )
        
        if response.status_code == 200:
            item = response.json()
            print(f"✓ Laundry item created successfully")
            print(f"  Item ID: {item['id']}")
            print(f"  Name: {item['name']}")
            print(f"  Category: {item['category']}")
            print(f"  Price: ₹{item['price_per_piece']}")
            self.created_items.append(item["id"])
            return True
        else:
            print(f"✗ Failed to create laundry item: {response.text}")
            return False
    
    def test_create_laundry_order(self):
        """Test creating a laundry order"""
        print("\n=== Testing Create Laundry Order ===")
        if not self.laundry_vendor_id or not self.created_items:
            print("✗ Missing laundry vendor ID or items")
            return False
        
        # First create a user for testing
        user_token, user = self.login("comm@test.com", "test")  # Use existing user
        if not user_token:
            print("✗ Failed to get user token for order creation")
            return False
        
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        order_data = {
            "laundry_vendor_id": self.laundry_vendor_id,
            "pickup_address": "Apartment A-101, Green Valley Community",
            "pickup_date": tomorrow.isoformat(),
            "pickup_time_slot": "10:00-12:00",
            "pickup_instructions": "Please call before arriving",
            "delivery_address": "Same as pickup address",
            "delivery_instructions": "Ring doorbell twice",
            "items": [
                {
                    "laundry_item_id": self.created_items[0],
                    "quantity": 2,
                    "special_instructions": "Handle with care"
                },
                {
                    "laundry_item_id": self.created_items[1] if len(self.created_items) > 1 else self.created_items[0],
                    "quantity": 1,
                    "special_instructions": "No starch please"
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/laundry/orders",
            json=order_data,
            headers=self.get_auth_headers(user_token)
        )
        
        if response.status_code == 200:
            order = response.json()
            print(f"✓ Laundry order created successfully")
            print(f"  Order ID: {order['id']}")
            print(f"  Order Number: {order['order_number']}")
            print(f"  Status: {order['status']}")
            print(f"  Total Amount: ₹{order['total_amount']}")
            print(f"  Items: {len(order['items'])}")
            self.created_orders.append(order["id"])
            return True
        else:
            print(f"✗ Failed to create laundry order: {response.text}")
            return False
    
    def test_update_order_status(self):
        """Test updating order status"""
        print("\n=== Testing Update Order Status ===")
        if not self.created_orders or not self.vendor_token:
            print("✗ No orders to update or missing vendor token")
            return False
        
        order_id = self.created_orders[0]
        
        # Update order status to confirmed
        response = requests.put(
            f"{BASE_URL}/laundry/orders/{order_id}",
            json={"status": "confirmed"},
            headers=self.get_auth_headers(self.vendor_token)
        )
        
        if response.status_code == 200:
            order = response.json()
            print(f"✓ Order status updated successfully")
            print(f"  Order ID: {order['id']}")
            print(f"  New Status: {order['status']}")
            print(f"  Confirmed At: {order.get('confirmed_at', 'Not set')}")
            return True
        else:
            print(f"✗ Failed to update order status: {response.text}")
            return False
    
    def test_process_payment(self):
        """Test processing payment for an order"""
        print("\n=== Testing Process Payment ===")
        if not self.created_orders:
            print("✗ No orders available for payment")
            return False
        
        # Use user token for payment
        user_token, _ = self.login("comm@test.com", "test")
        if not user_token:
            print("✗ Failed to get user token for payment")
            return False
        
        order_id = self.created_orders[0]
        payment_data = {
            "payment_method": "dummy"
        }
        
        response = requests.post(
            f"{BASE_URL}/laundry/orders/{order_id}/payment",
            json=payment_data,
            headers=self.get_auth_headers(user_token)
        )
        
        if response.status_code == 200:
            payment = response.json()
            print(f"✓ Payment processed successfully")
            print(f"  Success: {payment['success']}")
            print(f"  Payment Reference: {payment['payment_reference']}")
            print(f"  Message: {payment['message']}")
            return True
        else:
            print(f"✗ Failed to process payment: {response.text}")
            return False
    
    def test_vendor_dashboard(self):
        """Test vendor dashboard"""
        print("\n=== Testing Vendor Dashboard ===")
        if not self.laundry_vendor_id or not self.vendor_token:
            print("✗ Missing laundry vendor ID or vendor token")
            return False
        
        response = requests.get(
            f"{BASE_URL}/laundry/vendors/{self.laundry_vendor_id}/dashboard",
            headers=self.get_auth_headers(self.vendor_token)
        )
        
        if response.status_code == 200:
            dashboard = response.json()
            print(f"✓ Vendor dashboard retrieved successfully")
            print(f"  Total Orders: {dashboard['total_orders']}")
            print(f"  Pending Orders: {dashboard['pending_orders']}")
            print(f"  Today's Revenue: ₹{dashboard['today_revenue']}")
            print(f"  Monthly Revenue: ₹{dashboard['monthly_revenue']}")
            print(f"  Active Items: {dashboard['active_items']}")
            print(f"  Recent Orders: {len(dashboard['recent_orders'])}")
            return True
        else:
            print(f"✗ Failed to get vendor dashboard: {response.text}")
            return False
    
    def test_user_dashboard(self):
        """Test user dashboard"""
        print("\n=== Testing User Dashboard ===")
        user_token, _ = self.login("comm@test.com", "test")
        if not user_token:
            print("✗ Failed to get user token")
            return False
        
        response = requests.get(
            f"{BASE_URL}/laundry/users/dashboard",
            headers=self.get_auth_headers(user_token)
        )
        
        if response.status_code == 200:
            dashboard = response.json()
            print(f"✓ User dashboard retrieved successfully")
            print(f"  Total Orders: {dashboard['total_orders']}")
            print(f"  Pending Orders: {dashboard['pending_orders']}")
            print(f"  Delivered Orders: {dashboard['delivered_orders']}")
            print(f"  Total Spent: ₹{dashboard['total_spent']}")
            print(f"  Favorite Vendor: {dashboard.get('favorite_vendor', 'None')}")
            print(f"  Recent Orders: {len(dashboard['recent_orders'])}")
            return True
        else:
            print(f"✗ Failed to get user dashboard: {response.text}")
            return False
    
    def test_get_orders(self):
        """Test getting orders with different filters"""
        print("\n=== Testing Get Orders ===")
        
        # Test with user token
        user_token, _ = self.login("comm@test.com", "test")
        if user_token:
            response = requests.get(
                f"{BASE_URL}/laundry/orders",
                headers=self.get_auth_headers(user_token)
            )
            
            if response.status_code == 200:
                orders = response.json()
                print(f"✓ User orders retrieved: {len(orders)} orders")
            else:
                print(f"✗ Failed to get user orders: {response.text}")
        
        # Test with vendor token
        if self.vendor_token and self.laundry_vendor_id:
            response = requests.get(
                f"{BASE_URL}/laundry/orders?vendor_id={self.laundry_vendor_id}",
                headers=self.get_auth_headers(self.vendor_token)
            )
            
            if response.status_code == 200:
                orders = response.json()
                print(f"✓ Vendor orders retrieved: {len(orders)} orders")
                return True
            else:
                print(f"✗ Failed to get vendor orders: {response.text}")
                return False
        
        return True
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🧪 Starting Comprehensive Laundry API Tests")
        print("=" * 50)
        print("🔧 Using X-Testing header for localhost testing (bypasses authentication)")
        print("=" * 50)
        
        tests = [
            ("Master Login", self.test_master_login),
            ("Create Vendor with Auto-Login", self.test_create_vendor),
            ("Vendor Login", self.test_vendor_login),
            ("Get Laundry Vendors", self.test_get_laundry_vendors),
            ("Get Laundry Items", self.test_get_laundry_items),
            ("Create Laundry Item", self.test_create_laundry_item),
            ("Create Laundry Order", self.test_create_laundry_order),
            ("Update Order Status", self.test_update_order_status),
            ("Process Payment", self.test_process_payment),
            ("Vendor Dashboard", self.test_vendor_dashboard),
            ("User Dashboard", self.test_user_dashboard),
            ("Get Orders", self.test_get_orders),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"✗ {test_name} failed with exception: {str(e)}")
                failed += 1
            
            time.sleep(1)  # Brief pause between tests
        
        print("\n" + "=" * 50)
        print(f"🎯 Test Results: {passed} passed, {failed} failed")
        print("=" * 50)
        
        if self.created_orders:
            print(f"\n📝 Created Orders for Testing: {self.created_orders}")
        if self.vendor_id:
            print(f"🏪 Created Vendor ID: {self.vendor_id}")
            print(f"🧺 Laundry Vendor ID: {self.laundry_vendor_id}")
        
        print(f"\n🔑 Auto-generated Vendor Login:")
        print(f"   Email: quickwash_laundry@vendor.test")
        print(f"   Password: test")
        
        return passed, failed

def main():
    """Main function to run the tests"""
    print("Starting Laundry API Test Suite...")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Server is not responding properly")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
        return
    
    print("✅ Server is running, starting tests...\n")
    
    tester = LaundryAPITester()
    passed, failed = tester.run_all_tests()
    
    if failed == 0:
        print("\n🎉 All tests passed! The laundry system is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
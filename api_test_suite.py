#!/usr/bin/env python3
"""
CommunityExpress API Test Suite
Comprehensive testing of all API endpoints with JSON output
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class APITestSuite:
    def __init__(self, base_url: str = "http://localhost:8004"):
        self.base_url = base_url
        self.token = None
        self.headers = {}
        self.test_results = {
            "test_session": {
                "timestamp": datetime.now().isoformat(),
                "base_url": base_url,
                "total_endpoints": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0.0
            },
            "endpoints": []
        }
        
    def log_test(self, endpoint: str, method: str, status_code: int, 
                 response_time: float, success: bool, response_data: Any = None, 
                 error: str = None, request_data: Any = None):
        """Log test result"""
        result = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time_ms": round(response_time * 1000, 2),
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "request_data": request_data,
            "response_data": response_data,
            "error": error
        }
        self.test_results["endpoints"].append(result)
        
        if success:
            self.test_results["test_session"]["passed"] += 1
        else:
            self.test_results["test_session"]["failed"] += 1
            
        self.test_results["test_session"]["total_endpoints"] += 1
        
    def authenticate(self):
        """Authenticate and get JWT token"""
        print("🔐 Authenticating...")
        
        # First, try to register a test user
        register_url = f"{self.base_url}/auth/register"
        register_data = {
            "email": "test@example.com", 
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
            "role": "master"
        }
        
        try:
            requests.post(register_url, json=register_data)
        except:
            pass  # User might already exist
        
        # Now login
        url = f"{self.base_url}/auth/login"
        data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        start_time = time.time()
        try:
            response = requests.post(url, json=data)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.log_test("/auth/login", "POST", response.status_code, 
                            response_time, True, result, request_data=data)
                print("✅ Authentication successful")
                return True
            else:
                self.log_test("/auth/login", "POST", response.status_code, 
                            response_time, False, response.text, 
                            f"Login failed: {response.status_code}", data)
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("/auth/login", "POST", 0, response_time, False, 
                        None, str(e), data)
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_endpoint(self, endpoint: str, method: str = "GET", 
                     data: Dict = None, params: Dict = None, 
                     description: str = ""):
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        print(f"🧪 Testing {method} {endpoint} - {description}")
        
        start_time = time.time()
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response_time = time.time() - start_time
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            success = 200 <= response.status_code < 300
            status_icon = "✅" if success else "❌"
            
            self.log_test(endpoint, method, response.status_code, response_time, 
                         success, response_data, 
                         None if success else f"HTTP {response.status_code}", 
                         data or params)
            
            print(f"   {status_icon} {response.status_code} ({response_time*1000:.0f}ms)")
            
            return success, response_data
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(endpoint, method, 0, response_time, False, 
                         None, str(e), data or params)
            print(f"   ❌ Error: {e}")
            return False, None
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting CommunityExpress API Test Suite")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return
            
        print("\n📊 Testing Dashboard Endpoints")
        print("-" * 40)
        self.test_endpoint("/dashboard/stats", "GET", description="Dashboard statistics")
        self.test_endpoint("/dashboard/recent-orders", "GET", description="Recent orders")
        self.test_endpoint("/dashboard/top-vendors", "GET", description="Top vendors")
        self.test_endpoint("/dashboard/revenue-trends", "GET", description="Revenue trends")
        
        print("\n🏘️  Testing Community Endpoints")
        print("-" * 40)
        self.test_endpoint("/communities", "GET", description="List all communities")
        
        # Test community creation
        community_data = {
            "name": f"Test Community {int(time.time())}",
            "description": "Test community created by API test suite",
            "location": "Test Location",
            "contact_email": "test@example.com"
        }
        success, community_result = self.test_endpoint("/communities", "POST", 
                                                      community_data, 
                                                      description="Create new community")
        
        community_id = None
        if success and community_result:
            community_id = community_result.get("id")
            if community_id:
                self.test_endpoint(f"/communities/{community_id}", "GET", 
                                 description="Get community by ID")
                
                # Update community
                update_data = {
                    "name": f"Updated Test Community {int(time.time())}",
                    "description": "Updated by API test suite"
                }
                self.test_endpoint(f"/communities/{community_id}", "PUT", 
                                 update_data, description="Update community")
        
        print("\n🏪 Testing Vendor Endpoints")
        print("-" * 40)
        self.test_endpoint("/vendors", "GET", description="List all vendors")
        self.test_endpoint("/vendors/stats", "GET", description="Vendor statistics")
        self.test_endpoint("/vendors/search", "GET", 
                          params={"q": "test"}, description="Search vendors")
        self.test_endpoint("/vendors/by-type", "GET", 
                          params={"vendor_type": "restaurant"}, 
                          description="Get vendors by type")
        
        # Test vendor creation if we have a community
        if community_id:
            vendor_data = {
                "name": f"Test Vendor {int(time.time())}",
                "type": "restaurant",
                "email": "vendor@test.com",
                "phone": "123-456-7890",
                "address": "123 Test Street",
                "community_id": community_id,
                "description": "Test vendor created by API suite"
            }
            success, vendor_result = self.test_endpoint("/vendors", "POST", 
                                                       vendor_data, 
                                                       description="Create new vendor")
            
            vendor_id = None
            if success and vendor_result:
                vendor_id = vendor_result.get("id")
                if vendor_id:
                    self.test_endpoint(f"/vendors/{vendor_id}", "GET", 
                                     description="Get vendor by ID")
        
        print("\n📦 Testing Product Endpoints")
        print("-" * 40)
        self.test_endpoint("/products", "GET", description="List all products")
        self.test_endpoint("/products/categories", "GET", description="Product categories")
        self.test_endpoint("/products/search", "GET", 
                          params={"q": "test"}, description="Search products")
        
        print("\n📋 Testing Order Endpoints")
        print("-" * 40)
        self.test_endpoint("/orders", "GET", description="List all orders")
        self.test_endpoint("/orders/stats", "GET", description="Order statistics")
        
        print("\n💳 Testing Payment Endpoints")
        print("-" * 40)
        self.test_endpoint("/payments", "GET", description="List all payments")
        self.test_endpoint("/payments/stats", "GET", description="Payment statistics")
        
        print("\n🔐 Testing Auth Endpoints")
        print("-" * 40)
        self.test_endpoint("/auth/me", "GET", description="Get current user")
        
        # Calculate success rate
        total = self.test_results["test_session"]["total_endpoints"]
        passed = self.test_results["test_session"]["passed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        self.test_results["test_session"]["success_rate"] = round(success_rate, 2)
        
        print("\n" + "=" * 60)
        print("📈 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Endpoints Tested: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {self.test_results['test_session']['failed']}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Save results to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"api_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        
        # Clean up test data if created
        if community_id:
            print(f"\n🧹 Cleaning up test community: {community_id}")
            self.test_endpoint(f"/communities/{community_id}", "DELETE", 
                             description="Cleanup test community")
        
        return self.test_results

def main():
    """Main function to run the test suite"""
    print("CommunityExpress API Test Suite")
    print("Comprehensive testing with JSON output")
    print()
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8004/docs")
        if response.status_code != 200:
            print("❌ Server not responding at localhost:8004")
            print("Please make sure the FastAPI server is running")
            return
    except:
        print("❌ Cannot connect to server at localhost:8004")
        print("Please make sure the FastAPI server is running")
        return
    
    # Run tests
    suite = APITestSuite()
    results = suite.run_all_tests()
    
    print("\n🎉 Test suite completed!")
    return results

if __name__ == "__main__":
    main()

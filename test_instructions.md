# Laundry System API Testing Instructions

## 🚀 Quick Start Testing Guide

### 1. Start the FastAPI Server
```bash
cd /Users/harsha/CommunityExpress/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Run Database Migration (if not done already)
```bash
python migrate_laundry.py
```

### 3. Test Auto-Generated Vendor Login

#### Step 1: Login as Master
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "master@test.com",
    "password": "master123"
  }'
```

Save the `access_token` from the response.

#### Step 2: Create a Laundry Vendor (this will auto-generate login credentials)
```bash
curl -X POST "http://localhost:8000/vendors/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_MASTER_TOKEN" \
  -d '{
    "name": "QuickWash Laundry",
    "type": "laundry",
    "community_id": "YOUR_COMMUNITY_ID",
    "description": "Professional laundry services with pickup and delivery"
  }'
```

This will automatically create:
- A user account with email: `quickwash_laundry@vendor.test`
- Default password: `test`
- A laundry vendor profile
- Default laundry items (8 items with different categories)

#### Step 3: Test Vendor Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "quickwash_laundry@vendor.test",
    "password": "test"
  }'
```

Save the vendor `access_token`.

### 4. Test Laundry APIs

#### Option A: Using Testing Header (Localhost Only)
For development/testing, you can use the `X-Testing: true` header to bypass authentication:

> **⚠️ IMPORTANT**: The `X-Testing: true` header only works when making requests from localhost (127.0.0.1, localhost, ::1). This is a security feature to prevent bypassing authentication in production environments.

#### Get Laundry Vendors (Testing Mode)
```bash
curl -X GET "http://localhost:8000/laundry/vendors" \
  -H "Content-Type: application/json" \
  -H "X-Testing: true"
```

#### Option B: Using Authorization (Production Mode)
#### Get Laundry Vendors (With Auth)
```bash
curl -X GET "http://localhost:8000/laundry/vendors" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Laundry Items (Testing Mode)
```bash
curl -X GET "http://localhost:8000/laundry/vendors/VENDOR_ID/items" \
  -H "Content-Type: application/json" \
  -H "X-Testing: true"
```

#### Create New Laundry Item (Testing Mode)
```bash
curl -X POST "http://localhost:8000/laundry/vendors/VENDOR_ID/items" \
  -H "Content-Type: application/json" \
  -H "X-Testing: true" \
  -d '{
    "name": "Premium Suit",
    "description": "High-end suit dry cleaning",
    "category": "dry_clean",
    "price_per_piece": 200.00,
    "estimated_time_hours": 48
  }'
```

#### Create Laundry Order (Testing Mode)
```bash
curl -X POST "http://localhost:8000/laundry/orders" \
  -H "Content-Type: application/json" \
  -H "X-Testing: true" \
  -d '{
    "laundry_vendor_id": "VENDOR_ID",
    "pickup_address": "Apartment A-101, Green Valley Community",
    "pickup_date": "2025-01-05",
    "pickup_time_slot": "10:00-12:00",
    "pickup_instructions": "Please call before arriving",
    "items": [
      {
        "laundry_item_id": "ITEM_ID",
        "quantity": 2,
        "special_instructions": "Handle with care"
      }
    ]
  }'
```

#### Update Order Status (Testing Mode)
```bash
curl -X PUT "http://localhost:8000/laundry/orders/ORDER_ID" \
  -H "Content-Type: application/json" \
  -H "X-Testing: true" \
  -d '{
    "status": "confirmed"
  }'
```

#### Process Payment (Testing Mode)
```bash
curl -X POST "http://localhost:8000/laundry/orders/ORDER_ID/payment" \
  -H "Content-Type: application/json" \
  -H "X-Testing: true" \
  -d '{
    "payment_method": "dummy"
  }'
```

#### Get Vendor Dashboard (Testing Mode)
```bash
curl -X GET "http://localhost:8000/laundry/vendors/VENDOR_ID/dashboard" \
  -H "Content-Type: application/json" \
  -H "X-Testing: true"
```

#### Get User Dashboard (Testing Mode)
```bash
curl -X GET "http://localhost:8000/laundry/users/dashboard" \
  -H "Content-Type: application/json" \
  -H "X-Testing: true"
```

### 5. Run Automated Test Script
```bash
python3 test_laundry_apis.py
```

## 🧪 What Gets Auto-Created

When you create a laundry vendor through the master interface, the system automatically creates:

### User Account
- **Email**: `{vendor_name}@vendor.test` (spaces replaced with underscores)
- **Password**: `test`
- **Role**: `vendor`
- **Community**: Same as specified in vendor creation

### Laundry Vendor Profile
- **Business Name**: Same as vendor name
- **Pickup Time**: 8:00 AM - 6:00 PM
- **Delivery Time**: 24 hours
- **Minimum Order**: ₹100
- **Pickup Charge**: ₹20
- **Delivery Charge**: ₹30

### Default Laundry Items (8 items)
1. **Men's Shirt** - Wash & Iron - ₹25
2. **Women's Shirt** - Wash & Iron - ₹30
3. **Trousers** - Wash & Iron - ₹35
4. **Jeans** - Wash Only - ₹40
5. **T-Shirt** - Wash & Fold - ₹20
6. **Suit** - Dry Clean - ₹150
7. **Dress** - Dry Clean - ₹120
8. **Bedsheet** - Wash & Fold - ₹50

## 📱 Frontend Testing

### User App Testing
1. Login with user credentials (e.g., `comm@test.com` / `test`)
2. Navigate to Laundry Services
3. Select a vendor and browse items
4. Add items to cart with quantities
5. Proceed to booking with pickup details
6. Complete dummy payment
7. Track order status

### Vendor App Testing
1. Login with auto-generated vendor credentials
2. Access vendor dashboard to see statistics
3. Manage orders (update status, view details)
4. Manage items (add new, edit pricing, toggle availability)
5. View revenue and order analytics

## 🔧 API Endpoints Summary

### Vendor Management
- `POST /vendors/` - Create vendor (auto-creates login)
- `GET /laundry/vendors` - List laundry vendors
- `GET /laundry/vendors/{id}` - Get vendor details

### Item Management
- `GET /laundry/vendors/{id}/items` - List items
- `POST /laundry/vendors/{id}/items` - Create item
- `PUT /laundry/vendors/{id}/items/{item_id}` - Update item
- `DELETE /laundry/vendors/{id}/items/{item_id}` - Delete item

### Order Management
- `POST /laundry/orders` - Create order
- `GET /laundry/orders` - List orders (filtered by role)
- `GET /laundry/orders/{id}` - Get order details
- `PUT /laundry/orders/{id}` - Update order status

### Payment
- `POST /laundry/orders/{id}/payment` - Process payment

### Dashboard
- `GET /laundry/vendors/{id}/dashboard` - Vendor analytics
- `GET /laundry/users/dashboard` - User statistics

## ✅ Expected Test Results

All APIs should return proper HTTP status codes:
- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found

The system maintains proper role-based access control and data integrity throughout all operations.
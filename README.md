# CommunityExpress API

FastAPI backend for the CommunityExpress community marketplace application.

## Features

- **Authentication**: JWT-based authentication with role-based access control
- **User Management**: Support for Master, Admin, Partner, and User roles
- **Vendor Management**: Community-specific vendor onboarding and management
- **Product Catalog**: Product management by vendors
- **Order Management**: Complete order lifecycle management
- **Payment Processing**: Mock payment system for demo purposes
- **Community System**: Users join communities via unique codes

## User Roles

- **Master**: Platform administrator, can create communities and onboard vendors
- **Admin**: Community vendor manager, manages their specific vendor operations
- **Partner**: Workers under vendors, update order status and assignments
- **User**: Community residents, place orders and access services

## Vendor Types

- **Milk**: Daily delivery before 12am for next day morning delivery
- **Laundry**: Pickup and delivery service with item management
- **Food**: Instant delivery (10-15 mins) with multiple items
- **Cleaning**: Service booking with partner management

## Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

4. Run the application:
```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info
- `POST /auth/join-community` - Join community with code

### Vendors
- `GET /vendors/` - List vendors (filtered by community)
- `POST /vendors/` - Create vendor (master only)
- `GET /vendors/{vendor_id}` - Get vendor details
- `PUT /vendors/{vendor_id}` - Update vendor

### Products
- `GET /products/vendor/{vendor_id}` - Get products by vendor
- `POST /products/` - Create product (admin/master)
- `GET /products/{product_id}` - Get product details
- `PUT /products/{product_id}` - Update product
- `DELETE /products/{product_id}` - Delete product

### Orders
- `GET /orders/` - List orders (filtered by role)
- `POST /orders/` - Create order
- `GET /orders/{order_id}` - Get order details
- `PUT /orders/{order_id}/status` - Update order status

### Payments
- `GET /payments/` - List payments
- `POST /payments/` - Create payment (mock)
- `GET /payments/{payment_id}` - Get payment details
- `POST /payments/{payment_id}/refund` - Refund payment

## Database

The API uses Supabase (PostgreSQL) as the database. Run the migration script in the `database/` folder to set up the schema.

## Deployment

Deploy to Render.com:
1. Connect your GitHub repository
2. Set environment variables in Render dashboard
3. Use the following build command: `pip install -r requirements.txt`
4. Use the following start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Development

- API Documentation: Available at `/docs` when running the server
- Interactive API: Available at `/redoc` when running the server
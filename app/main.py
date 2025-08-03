from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, orders, vendors, products, payments

app = FastAPI(
    title="CommunityExpress API",
    description="Community marketplace application API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(vendors.router)
app.include_router(products.router)
app.include_router(payments.router)

@app.get("/")
async def root():
    return {"message": "Welcome to CommunityExpress API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "CommunityExpress API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
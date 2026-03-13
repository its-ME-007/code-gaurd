"""
Cloud Key Rotation Engine - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import routes
from app.db.init import initialize_database
import boto3

app = FastAPI(
    title="Cloud Key Rotation Engine",
    description="Deterministic AWS IAM Access Key Lifecycle Manager",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize boto3 session with explicit credentials from settings
boto3.setup_default_session(
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on app startup"""
    initialize_database()
    print("🚀 Cloud Key Rotation Engine started")

# Include routes
app.include_router(routes.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rotation-engine"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)

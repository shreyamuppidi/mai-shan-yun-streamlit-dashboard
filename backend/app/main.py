"""
FastAPI Backend for Mai Shan Yun Dashboard
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.api import routes

app = FastAPI(
    title="Mai Shan Yun Inventory Dashboard API",
    description="Backend API for restaurant inventory management dashboard",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Mai Shan Yun Dashboard API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


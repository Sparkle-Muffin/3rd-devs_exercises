from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

# Create FastAPI app instance
app = FastAPI(
    title="Task 24 API",
    description="A FastAPI application sketch",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Request(BaseModel):
    message: str

class Response(BaseModel):
    answer: str


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "message": "FastAPI application is running",
        "status": "ok",
        "version": "1.0.0"
    }


# Create new item
@app.post("/", response_model=Response, status_code=200)
async def handle_request(request: Request):
    """Response endpoint"""
    print(request)
    return Response(answer="Hello, World!")


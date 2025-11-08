from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

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

# Pydantic models for request/response
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None
    price_with_tax: float

# In-memory storage (for demo purposes)
items_db: List[ItemResponse] = []
next_id = 1

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "message": "FastAPI application is running",
        "status": "ok",
        "version": "1.0.0"
    }

# Get all items
@app.get("/items", response_model=List[ItemResponse])
async def get_items():
    """Get all items"""
    return items_db

# Get item by ID
@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """Get a specific item by ID"""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

# Create new item
@app.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(item: Item):
    """Create a new item"""
    global next_id
    tax = item.tax if item.tax is not None else 0.0
    price_with_tax = item.price * (1 + tax)
    
    new_item = ItemResponse(
        id=next_id,
        name=item.name,
        description=item.description,
        price=item.price,
        tax=tax,
        price_with_tax=price_with_tax
    )
    items_db.append(new_item)
    next_id += 1
    return new_item

# Delete item by ID
@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int):
    """Delete an item by ID"""
    global items_db
    original_length = len(items_db)
    items_db = [item for item in items_db if item.id != item_id]
    if len(items_db) == original_length:
        raise HTTPException(status_code=404, detail="Item not found")
    return None

# Example endpoint with path and query parameters
@app.get("/search")
async def search_items(q: Optional[str] = None, limit: int = 10):
    """Search items with query parameter"""
    if q:
        filtered = [item for item in items_db if q.lower() in item.name.lower()]
        return filtered[:limit]
    return items_db[:limit]


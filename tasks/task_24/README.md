# Task 24 - FastAPI and Uvicorn Application

A basic FastAPI application sketch with Uvicorn server.

## Installation

Install the required dependencies:

```bash
pip install fastapi uvicorn[standard]
```

## Running the Application

### Option 1: Using main.py
```bash
python main.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using uvicorn from command line
```bash
cd tasks/task_24
uvicorn app:app --reload
```

## API Endpoints

- `GET /` - Root endpoint (health check)
- `GET /items` - Get all items
- `GET /items/{item_id}` - Get item by ID
- `POST /items` - Create a new item
- `DELETE /items/{item_id}` - Delete an item by ID
- `GET /search?q={query}&limit={limit}` - Search items

## API Documentation

Once the server is running, you can access:
- Interactive API docs (Swagger UI): http://localhost:8000/docs
- Alternative API docs (ReDoc): http://localhost:8000/redoc

## Example Usage

### Create an item
```bash
curl -X POST "http://localhost:8000/items" \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "description": "Gaming laptop", "price": 1299.99, "tax": 0.23}'
```

### Get all items
```bash
curl "http://localhost:8000/items"
```

### Get item by ID
```bash
curl "http://localhost:8000/items/1"
```

### Search items
```bash
curl "http://localhost:8000/search?q=laptop&limit=5"
```


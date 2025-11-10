import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from pyngrok import conf, ngrok
sys.path.insert(0, str(os.getcwd()))
from common.centrala_aidevs_utils import AidevsMessageHandler
from dotenv import load_dotenv

load_dotenv()

task_name = os.getenv("TASK_24_TASK_NAME")
task_path = Path(__file__).parent
aidevs_msg_handler = AidevsMessageHandler(task_name, task_path)

ngrok_tunnel_url: Optional[str] = None
_ngrok_tunnel = None


def run_ngrok():
    global ngrok_tunnel_url, _ngrok_tunnel
    port = int(os.getenv("APP_PORT", "8666"))
    try:
        # _ngrok_tunnel = ngrok.connect(port, "http", bind_tls=True)
        _ngrok_tunnel = ngrok.connect(port, "http")
        ngrok_tunnel_url = _ngrok_tunnel.public_url
        os.environ["NGROK_TUNNEL_URL"] = ngrok_tunnel_url
        print(f"[ngrok] tunnel established -> {ngrok_tunnel_url}")
    except Exception as e:
        print(f"[ngrok] failed to establish tunnel: {e}")
        raise


def stop_ngrok():
    global ngrok_tunnel_url, _ngrok_tunnel
    if _ngrok_tunnel is not None:
        ngrok.disconnect(_ngrok_tunnel.public_url)
        ngrok.kill()
        _ngrok_tunnel = None
    if ngrok_tunnel_url is not None:
        os.environ.pop("NGROK_TUNNEL_URL", None)
        ngrok_tunnel_url = None


def send_my_api_to_centrala():
    message = ngrok_tunnel_url
    centrala_response = aidevs_msg_handler.ask_centrala_aidevs(message)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        run_ngrok()
        # send_my_api_to_centrala()
        yield
    finally:
        stop_ngrok()

# Create FastAPI app instance
app = FastAPI(
    title="Task 24 API",
    description="A FastAPI application sketch",
    version="1.0.0",
    lifespan=lifespan,
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
        "version": "1.0.0",
        "public_url": ngrok_tunnel_url,
    }


# Create new item
@app.post("/", response_model=Response, status_code=200)
async def handle_request(request: Request):
    """Response endpoint"""
    print(request)
    return Response(answer="Hello, World!")


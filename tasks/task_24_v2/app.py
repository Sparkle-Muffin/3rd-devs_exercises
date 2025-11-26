import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import asyncio
sys.path.insert(0, str(os.getcwd()))
from common.centrala_aidevs_utils import AidevsMessageHandler
from dotenv import load_dotenv
from common.logging import Logging
from classes import Response, Request
load_dotenv()

# Initialize directories
task_name = os.getenv("TASK_24_TASK_NAME")
task_path = Path(__file__).parent
tools_dir = task_path / "tools"
prompts_dir = task_path / "prompts"
downloads_dir = task_path / "downloads"
downloads_dir.mkdir(parents=True, exist_ok=True)
program_files_dir = task_path / "program_files"
program_files_dir.mkdir(parents=True, exist_ok=True)
questions_dir = task_path / "questions"
questions_dir.mkdir(parents=True, exist_ok=True)
answers_dir = task_path / "answers"
answers_dir.mkdir(parents=True, exist_ok=True)

# Initialize variables
aidevs_msg_handler = AidevsMessageHandler(task_name, task_path)
questions_logging = Logging(questions_dir)
answers_logging = Logging(answers_dir)
ngrok_tunnel_url: Optional[str] = None
_ngrok_tunnel = None
_announce_task: Optional[asyncio.Task] = None


# Create FastAPI app instance
app = FastAPI(
    title="Task 24 API",
    description="A FastAPI application sketch",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
async def handle_request(request: Request, fastapi_request: FastAPIRequest):
    try:
        # Log request
        questions_logging.log({
            "headers": dict(fastapi_request.headers),
            "body": request
        })


        loop = asyncio.get_running_loop()
        answer = await loop.run_in_executor(None, lambda: input("Enter your answer: "))
        # Log answer
        answers_logging.log(answer)

        answer = Response(answer=answer)
        return answer


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


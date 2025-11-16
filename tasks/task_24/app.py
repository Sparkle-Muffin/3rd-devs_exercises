import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from classes import Request, Response, State, Tool
from typing import Optional
from contextlib import asynccontextmanager, suppress
from pyngrok import ngrok
import asyncio
sys.path.insert(0, str(os.getcwd()))
from common.file_utils import read_file_content
from common.centrala_aidevs_utils import AidevsMessageHandler
from agent import Agent
from dotenv import load_dotenv

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

# Initialize variables
aidevs_msg_handler = AidevsMessageHandler(task_name, task_path)
ngrok_tunnel_url: Optional[str] = None
_ngrok_tunnel = None
_announce_task: Optional[asyncio.Task] = None


def run_ngrok():
    global ngrok_tunnel_url, _ngrok_tunnel
    port = int(os.getenv("APP_PORT", "8666"))
    try:
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
    aidevs_msg_handler.ask_centrala_aidevs(message)


async def _notify_centrala_when_ready(delay: float = 0.5):
    """Wait for the server to accept connections before notifying centrala."""
    await asyncio.sleep(delay)
    if ngrok_tunnel_url:
        # Run the synchronous HTTP request in a thread pool to avoid blocking the event loop
        await asyncio.to_thread(send_my_api_to_centrala)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _announce_task
    try:
        run_ngrok()
        _announce_task = asyncio.create_task(_notify_centrala_when_ready())
        yield
    finally:
        if _announce_task:
            _announce_task.cancel()
            with suppress(asyncio.CancelledError):
                await _announce_task
            _announce_task = None
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


file_downloader_instruction = read_file_content(tools_dir / "file_downloader/file_downloader_instruction.txt")
speech_to_text_tool_instruction = read_file_content(tools_dir / "speech_to_text_tool/speech_to_text_tool_instruction.txt")
answer_to_server_instruction = read_file_content(tools_dir / "answer_to_server/answer_to_server_instruction.txt")
return_flag_instruction = read_file_content(tools_dir / "return_flag/return_flag_instruction.txt")

# Initialize state
state: State = State(
    config={
        'max_steps': 20,
        'current_step': 0,
        'active_step': None
    },
    messages=[],
    tools=[
        Tool(
            name="no_tool_needed",
            description="Choose this option if no tool is needed and you can answer the question directly.",
            instruction="...",
        ),
        Tool(
            name="file_downloader",
            description="Use this tool to download files from the Internet. As a result, this tool provides a local path to a downloaded file.",
            instruction=file_downloader_instruction,
        ),
        Tool(
            name="speech_to_text_tool",
            description="Use this tool to transcript an audio file to text. File has to be downloaded first using file_downloader tool. As a result, this tool provides a transcripted file in a text string form.",
            instruction=speech_to_text_tool_instruction,
        ),
        Tool(
            name="answer_to_server",
            description="Use this tool to send the answer to the server.",
            instruction=answer_to_server_instruction,
        ),
        Tool(
            name="return_flag",
            description="Only use this tool once you have completed all tasks and captured the flag.",
            instruction=return_flag_instruction,
        ),
    ],
    actions=[],
)


agent = Agent(task_name, task_path, downloads_dir, program_files_dir, state)


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
    try:
        # Update state questions
        state.questions.append(request)
        
        next_move = None
        parameters = None
        for i in range(state.config["max_steps"]):
            # Make a plan
            next_move = await agent.plan()

            print('Thinking...', next_move.get('_reasoning'))
            print(f"Tool: {next_move.get('tool')}")
            print(f"Task description: {next_move.get('task_description')}")
                            
            # Set the active step
            state.config['active_step'] = {
                'name': next_move['tool'],
                'task_description': next_move['task_description']
            }
            if next_move.get('tool') == 'no_tool_needed':
                await agent.answer_the_question()
            else:
                # Generate the parameters for the tool
                parameters = await agent.describe(next_move['tool'], next_move['task_description'])
                # If there's no tool to use, we're done
                if next_move.get('tool') == 'answer_to_server' or next_move.get('tool') == 'return_flag':
                    break
                # Use the tool
                await agent.use_tool(next_move['tool'], parameters)
            # Increase the step counter
            state.config['current_step'] += 1

        # The loop has finished. Check if the agent decided on a final answer.
        if next_move and (next_move.get('tool') == 'answer_to_server' or next_move.get('tool') == 'return_flag'):
            # The 'parameters' from the 'describe' call should be a dict with the answer.
            final_answer_str = parameters.get('answer')

            # If the answer is not in the 'answer' key, maybe it's in 'flag' key
            if not final_answer_str:
                final_answer_str = parameters.get('flag')

            # If we still don't have an answer, something is wrong.
            # For safety, we can serialize the whole parameters dict to not lose information.
            if not final_answer_str:
                import json
                final_answer_str = json.dumps(parameters)

            answer = Response(answer=final_answer_str)
            state.answers.append(answer)
            return answer

        # If the loop finished without a decision to answer, it's an error state.
        raise HTTPException(status_code=500, detail="Agent could not determine an answer within the step limit.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


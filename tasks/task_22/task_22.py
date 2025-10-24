from pathlib import Path
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)
from common.file_utils import read_file_content
from classes import State, Tool, ChatRequest
from agent import Agent
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

task_name = os.getenv("TASK_22_TASK_NAME")
task_path = Path(__file__).parent

tools_dir = task_path / "tools"
people_search_instruction = read_file_content(tools_dir / "people_search/people_search_instruction.txt")
database_search_instruction = read_file_content(tools_dir / "database_search/database_search_instruction.txt")
gps_search_instruction = read_file_content(tools_dir / "gps_search/gps_search_instruction.txt")
get_flag_instruction = read_file_content(tools_dir / "get_flag/get_flag_instruction.txt")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize state
state: State = State(
    config={
        'max_steps': 10,
        'current_step': 0,
        'active_step': None
    },
    messages=[],
    tools=[
        Tool(
            name="people_search",
            description="This is a tool that returns names of people connected with a certain Polish city. This it the ONLY tool that connects people with cities.",
            instruction=people_search_instruction,
        ),
        Tool(
            name="database_search",
            description="This is a tool that enables sending queries to a MySQL database. The database contains information about people e.g. their ID.",
            instruction=database_search_instruction,
        ),
        Tool(
            name="gps_search",
            description="This is a tool that returns latitude and longitude for a given ID of a person.",
            instruction=gps_search_instruction,
        ),
        Tool(
            name="get_flag",
            description="This is a tool that sends coordinates to a server and returns a flag.",
            instruction=get_flag_instruction,
        ),
        Tool(
            name="final_answer",
            description="Use this tool when you completed the task successfully to write a message to a user.",
            instruction="...",
        ),
    ],
    actions=[],
)


@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        # Update state messages
        if len(request.messages) == 1:
            state.messages.extend([
                msg for msg in request.messages
                if msg.get('role') != 'system'
            ])
        else:
            state.messages = [
                msg for msg in request.messages
                if msg.get('role') != 'system'
            ]

        agent = Agent(task_name, task_path, state)
        
        for i in range(state.config["max_steps"]):
            # Make a plan
            next_move = await agent.plan()
            if not next_move:
                break

            print('Thinking...', next_move.get('_reasoning'))
            print(f"Tool: {next_move.get('tool')}")
            print(f"Task description: {next_move.get('task_description')}")
                            
            # Set the active step
            state.config['active_step'] = {
                'name': next_move['tool'],
                'task_description': next_move['task_description']
            }
            # If there's no tool to use, we're done
            if not next_move.get('tool') or next_move.get('tool') == 'final_answer':
                break
            # Generate the parameters for the tool
            parameters = await agent.describe(next_move['tool'], next_move['task_description'])
            # Use the tool
            await agent.use_tool(next_move['tool'], parameters)
            # Increase the step counter
            state.config['current_step'] += 1


        # Generate the answer
        answer = await agent.generate_answer()
        
        state.messages.append(answer)
        
        return answer

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Agent API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)

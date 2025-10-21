from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]

class ChatResponse(BaseModel):
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, Any]] = None

class Action(BaseModel):
    uuid: str
    name: str
    parameters: str
    description: str
    results: str

class Tool(BaseModel):
    name: str
    description: str
    instruction: str

class State(BaseModel):
    messages: List[Dict[str, Any]]
    tools: List[Tool]
    actions: List[Action]
    config: Dict[str, Any]
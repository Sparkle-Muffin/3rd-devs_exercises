from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class Request(BaseModel):
    question: str

class Response(BaseModel):
    answer: str

class Action(BaseModel):
    uuid: str
    name: str
    query: str
    results: str

class Tool(BaseModel):
    name: str
    description: str
    instruction: str

class State(BaseModel):
    questions: List[Dict[str, Any]]
    answers: List[Dict[str, Any]]
    tools: List[Tool]
    actions: List[Action]
    config: Dict[str, Any]
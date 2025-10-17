from pydantic import BaseModel
from typing import List, Optional, Dict


class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]] = []  # Optional conversation history


class AgentStep(BaseModel):
    agent: str
    action: str
    result: Optional[str] = None
    elapsed_time: Optional[float] = None  # Agent execution time in seconds
    input: Optional[str] = None  # Agent input data
    output: Optional[str] = None  # Agent output data


class ChatResponse(BaseModel):
    response: str
    steps: List[AgentStep]
    elapsed_time: Optional[float] = None  # Processing time in seconds (0.1s precision)


class AgentInfo(BaseModel):
    name: str
    description: str
    order: int


class WorkflowInfo(BaseModel):
    agents: List[AgentInfo]
    description: str

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class UserPersona(BaseModel):
    id: str
    name: str
    description: str
    patience: float = Field(ge=0, le=1, description="0 = very impatient, 1 = very patient")
    expertise: float = Field(ge=0, le=1, description="0 = novice, 1 = expert")
    verbosity: float = Field(ge=0, le=1, description="0 = concise, 1 = verbose")
    frustration_tolerance: float = Field(ge=0, le=1, description="0 = easily frustrated, 1 = high tolerance")
    clarity_of_communication: float = Field(ge=0, le=1, description="0 = unclear, 1 = very clear")
    technical_level: float = Field(ge=0, le=1, description="0 = non-technical, 1 = highly technical")


class ConversationGoal(BaseModel):
    id: str
    description: str
    success_criteria: List[str]
    expected_turns: Optional[int] = None
    domain: Literal['technical', 'general', 'business', 'creative', 'educational']
    complexity: Literal['simple', 'moderate', 'complex']


class Message(BaseModel):
    role: Literal['user', 'assistant']
    content: str
    timestamp: datetime
    turn_number: int


class ConversationState(BaseModel):
    messages: List[Message]
    current_turn: int
    goal_progress: float = Field(ge=0, le=1)
    user_satisfaction: float = Field(ge=0, le=1)
    frustration_level: float = Field(ge=0, le=1)
    context: Optional[Dict[str, Any]] = None


class SimulationConfig(BaseModel):
    persona: UserPersona
    goal: ConversationGoal
    max_turns: int = 20
    api_endpoint: str
    simulation_id: str
    seed: Optional[int] = None


class EvaluationMetrics(BaseModel):
    goal_achieved: bool
    total_turns: int
    average_response_time: float
    user_satisfaction_score: float = Field(ge=0, le=1)
    clarity_score: float = Field(ge=0, le=1)
    relevance_score: float = Field(ge=0, le=1)
    completeness_score: float = Field(ge=0, le=1)
    frustration_incidents: int
    error_rate: float = Field(ge=0, le=1)


class SimulationResult(BaseModel):
    config: SimulationConfig
    conversation: ConversationState
    metrics: EvaluationMetrics
    start_time: datetime
    end_time: datetime
    duration: float  # in milliseconds
    errors: Optional[List[str]] = None
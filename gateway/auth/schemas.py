"""
Pydantic schemas for chat completion API.

Defines request and response models matching OpenAI's chat completion API format.
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional


class Role(str, Enum):
    """Valid message roles in a chat conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""
    role: Role
    content: str = Field(..., description="The content of the message")


class ChatUsage(BaseModel):
    """Token usage statistics for a completion request."""
    prompt_tokens: int = Field(0, description="Number of tokens in the prompt")
    completion_tokens: int = Field(0, description="Number of tokens in the completion")
    total_tokens: int = Field(0, description="Total tokens used (prompt + completion)")


class ChatChoice(BaseModel):
    """A single completion choice returned by the model."""
    index: int = Field(0, description="Index of this choice in the list")
    message: ChatMessage = Field(..., description="The generated message")
    finish_reason: str = Field("stop", description="Reason the model stopped generating")


class ChatRequest(BaseModel):
    """Request schema for chat completion endpoint."""
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    model: Optional[str] = Field(None, description="Model to use (optional, server default if not specified)")
    max_tokens: int = Field(100, ge=1, le=8192, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")


class ChatResponse(BaseModel):
    """Response schema for chat completion endpoint."""
    id: str = Field(..., description="Unique identifier for this completion")
    object: str = Field(..., description="Object type (always 'chat.completion')")
    created: int = Field(..., description="Unix timestamp of when the completion was created")
    model: str = Field(..., description="Model used for the completion")
    choices: List[ChatChoice] = Field(..., description="List of completion choices")
    usage: ChatUsage = Field(..., description="Token usage statistics")

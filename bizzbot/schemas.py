from datetime import datetime
from pydantic import BaseModel


class ClientChat(BaseModel):
    topic: str | None = None
    chat_id: str | None = None
    role: str
    content: str
    temporary: bool = False

    model_config = {
        "arbitrary_types_allowed": True
    }


class MessageModel(BaseModel):
    summary: str | None = None
    role: str
    content: str | list[str]


class PromptTopic(BaseModel):
    prompt: str
    topic: str


class Summary(BaseModel):
    summary: str | None = None


# class RagPrompt(BaseModel):
#     message: dict[Summary | list[MessageModel]]


class ChatsResponse(BaseModel):
    id: str
    user_id: str
    topic: str
    total_conversations: int = 0
    summarised_messages: int = 0
    created_at: datetime
    last_updated: datetime

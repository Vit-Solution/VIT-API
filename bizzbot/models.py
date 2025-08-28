from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field


class Message(BaseModel):
    id: ObjectId = Field(alias="_id")
    chat_id: ObjectId
    role: str
    content: str
    timestamp: datetime

    model_config = {
        "arbitrary_types_allowed": True,
        "populate_by_name": True
    }


class Chats(BaseModel):
    id: ObjectId = Field(alias="_id")
    user_id: ObjectId
    topic: str
    total_conversations: int = 0
    summarised_messages: int = 0
    created_at: datetime
    last_updated: datetime

    model_config = {
            "arbitrary_types_allowed": True,
            "populate_by_name": True
        }


class Summaries(BaseModel):
    id: ObjectId = Field(alias="_id")
    chat_id: ObjectId
    summary: str
    from_msg: int
    to_msg: int
    created_at: datetime

    model_config = {
            "arbitrary_types_allowed": True,
            "populate_by_name": True
        }

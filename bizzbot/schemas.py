from bson import ObjectId
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
    role: str
    content: str | list[str]


class PromptTopic(BaseModel):
    prompt: str
    topic: str


class Summary(BaseModel):
    summary: str | None = None


# class RagPrompt(BaseModel):
#     message: dict[Summary | list[MessageModel]]


class MyChats(BaseModel):
    user_id: str
    chats: dict[str, str] # chat_id: topic

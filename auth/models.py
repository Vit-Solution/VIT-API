from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    email: str | None = None
    id: str | None = None


class BusinessInformation(BaseModel):
    business_name: str | None = None
    business_type: str | None = None
    business_address: str | None = None
    business_description: str | None = None
    business_website: str | None = None


class Users(BaseModel):
    _id: ObjectId
    username: str | None = None
    full_name: str
    phone_number: str
    email: str
    business_info: BusinessInformation | None = None
    hashed_password: str
    created_at: datetime = datetime.now()
    updated_at: datetime
    last_login: datetime
    is_active: bool = True
    role: str = "user"


class Faqs(BaseModel):
    _id: ObjectId
    category: str
    question: str
    answer: str
    tags: list[str]
    source: str
    created_at: datetime
    updated_at: datetime
    related_questions: list[str]


class Message(BaseModel):
    _id: ObjectId
    role: str  # "user" or "bizzbot"
    content: str
    timestamp: datetime
    # [
    #     {"role": "user", "content": "How do I register a business?"},
    #     {"role": "assistant", "content": "Here are the steps..."}
    # ],


# index on user_id and last_updated for faster retrieval of recent chats
class Chats(BaseModel):
    _id: ObjectId
    user_id: str
    topic: str
    messages: list[Message]
    created_at: datetime
    last_updated: datetime


class ErrorLogs(BaseModel):
    _id: ObjectId
    event_type: str  # "ERROR" | "INFO" | "REQUEST"
    message: str
    metadata: dict
    timestamp: datetime

    # metadata: {
    #     "user_id": ObjectId("ref to users._id"),
    #     "faq_id": ObjectId("ref to faqs._id")
    # }

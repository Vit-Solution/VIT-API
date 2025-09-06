from datetime import datetime, timezone
import time
from bson import ObjectId
from fastapi import HTTPException
from config import RAG_API_URL
import httpx
from bizzbot.schemas import ClientChat, MessageModel, PromptTopic
from bizzbot.models import Chats, Message, Summaries
from auth.db_connection import chats_collection, messages_collection, summaries_collection


# ----------------------- QUERY RAG API -----------------------
async def query_rag_api(prompt: MessageModel | list[MessageModel]) -> MessageModel:
    if isinstance(prompt, list):
        prompt_json = {"messages": [p.model_dump() for p in prompt]}
    else:
        prompt_json = {"messages": prompt.model_dump()}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Forward request to external RAG API
            response = await client.post(
                RAG_API_URL,
                headers={"accept": "application/json", "Content-Type": "application/json"},
                json=prompt_json
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Upstream API error: {e}")
        
        result: dict = response.json()
        data: dict = result.get("message", {})

        return MessageModel(
            role=data.get("role", "assistant"),
            content=data.get("content", "")
        )


# ----------------------- GET TOPIC FROM RAG API -----------------------
async def get_chat_topic(prompt: ClientChat) -> PromptTopic:
    if not prompt.topic:
        prefix = "In three words or less, give a topic for conversations that may arise from this prompt: \n"
        new_prompt = MessageModel(role="user", content=prefix + prompt.content)

        result = await query_rag_api(new_prompt)

        return PromptTopic(
            prompt=prefix + prompt.content,
            topic=result.content
        )

    return PromptTopic(
        prompt=prompt.content,
        topic=prompt.topic
    )
    

# ----------------------- CREATE NEW CHAT -----------------------
def create_new_chat(user_id: str, topic: str, user_prompt_text: str, bot_response_text: str) -> bool:
    # new chat
    chat_details = Chats(
        id=ObjectId(),
        user_id=ObjectId(user_id),
        topic=topic,
        total_conversations=1,
        summarised_messages=0,
        created_at=datetime.now(timezone.utc),
        last_updated=datetime.now(timezone.utc)
    )

    # user prompt
    user_prompt = Message(
        id=ObjectId(),
        chat_id=chat_details.id,
        role="user",
        content=user_prompt_text,
        timestamp=datetime.now(timezone.utc)
    )
    
    # bot response
    bot_response = Message(
        id=ObjectId(),
        chat_id=chat_details.id,
        role="assistant",
        content=bot_response_text,
        timestamp=datetime.now(timezone.utc)
    )

    # store chat in db
    chat_insertion_id = chats_collection.insert_one(chat_details.model_dump(by_alias=True))
    
    # store message in db
    user_prompt_insertion_id = messages_collection.insert_one(user_prompt.model_dump(by_alias=True))
    # sleep 1 milisecond to achieve order by timestamp in query
    time.sleep(0.001)
    bot_response_insertion_id = messages_collection.insert_one(bot_response.model_dump(by_alias=True))

    if chat_insertion_id.inserted_id and user_prompt_insertion_id.inserted_id and bot_response_insertion_id.inserted_id:
        return True

    return False

def insert_existing_chats(new_prompt: ClientChat, response: MessageModel, updated_chat: Chats, summary: Summaries | None = None):
    new_prompt = Message(
        id=ObjectId(),
        chat_id=ObjectId(new_prompt.chat_id),
        role=new_prompt.role,
        content=new_prompt.content,
        timestamp=datetime.now(timezone.utc)
    )

    response = Message(
        id=ObjectId(),
        chat_id=ObjectId(new_prompt.chat_id),
        role=response.role,
        content=response.content,
        timestamp=datetime.now(timezone.utc)
    )


    inserted_prompt_id = messages_collection.insert_one(new_prompt.model_dump(by_alias=True)).inserted_id
    inserted_response_id = messages_collection.insert_one(response.model_dump(by_alias=True)).inserted_id

    if summary:
        inserted_summary_id = summaries_collection.insert_one(summary.model_dump(by_alias=True)).inserted_id
    
    chats_update = chats_collection.update_one(
        {"_id": updated_chat.id},
        {
            "$set": {
                "total_conversations": updated_chat.total_conversations,
                "summarised_messages": updated_chat.summarised_messages,
                "last_updated": updated_chat.last_updated
            }
        },
        upsert=False
    )
    
    if inserted_prompt_id and inserted_response_id and chats_update.modified_count == 1:
        return True

    return False

# ----------------------- GET CHAT BY ID FROM DB -----------------------
def get_chat_by_id(chat_id: str) -> Chats | None:
    """
    Retrieve a chat from the database by ID.

    :param chat_id: The ID of the chat to retrieve.
    :return: The chat as a dictionary, or None if the chat does not exist.
    """
    chat_details: dict = chats_collection.find_one({"_id": ObjectId(chat_id)})

    if chat_details:
        chat = Chats(
            id=chat_details["_id"],
            user_id=chat_details["user_id"],
            topic=chat_details["topic"],
            total_conversations=chat_details.get("total_conversations", 0),
            summarised_messages=chat_details.get("summarised_messages", 0),
            created_at=chat_details["created_at"],
            last_updated=chat_details["last_updated"]
        )

        return chat
    return None

from datetime import datetime, timezone
import time
from bson import ObjectId
from fastapi import HTTPException
from config import RAG_API_URL
import httpx
from bizzbot.schemas import ClientChat, MessageModel, PromptTopic
from bizzbot.models import Chats, Message
from auth.db_connection import chats_collection, messages_collection


# ----------------------- QUERY RAG API -----------------------
async def query_rag_api(prompt: MessageModel) -> MessageModel:
    return MessageModel(role="assistant", content="Topic 1")

    # async with httpx.AsyncClient(timeout=30.0) as client:
    #     try:
    #         # Forward request to external RAG API
    #         response = await client.post(
    #             RAG_API_URL,
    #             headers={"accept": "application/json", "Content-Type": "application/json"},
    #             json=prompt.model_dump()
    #         )
    #         response.raise_for_status()
    #     except httpx.HTTPError as e:
    #         raise HTTPException(status_code=502, detail=f"Upstream API error: {e}")
        
    #     result = response.json()

        # return MessageModel(
        #     role=result.get("role", "assistant"),
        #     content=result.get("content", "")
        # )


# ----------------------- GET TOPIC FROM RAG API -----------------------
async def get_chat_topic(prompt: ClientChat) -> PromptTopic:
    if prompt.topic is not None:
        return PromptTopic(
            prompt=prompt.content,
            topic=prompt.topic
        )
    
    prefix = "In three words or less, give a topic for conversations that may arise from this prompt: \n"
    prompt.content = prefix + prompt.content
    new_prompt = MessageModel(role="user", content=prompt.content)

    result = await query_rag_api(new_prompt)
    # sample_result = {
    #     "role": "assistant",
    #     "content": "Topic 1"
    # }

    return PromptTopic(
        prompt=prompt.content,
        topic=result.content
    )



def create_new_chat(user_id: str, topic: str, user_prompt_text: str, bot_response_text: str):
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

    # store chat and message details in db
    chat_insertion_id = chats_collection.insert_one(chat_details.model_dump(by_alias=True))
    # sleep 1 milisecond to enable achievement of order by timestamp in query
    time.sleep(0.001)
    user_prompt_insertion_id = messages_collection.insert_one(user_prompt.model_dump(by_alias=True))
    time.sleep(0.001)
    bot_response_insertion_id = messages_collection.insert_one(bot_response.model_dump(by_alias=True))

    if chat_insertion_id.inserted_id and user_prompt_insertion_id.inserted_id and bot_response_insertion_id.inserted_id:
        return chat_details

    return None



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

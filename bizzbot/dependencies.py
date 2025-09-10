from datetime import datetime, timezone
import time
from typing import Literal
from bson import ObjectId
from fastapi import HTTPException
from config import RAG_API_URL
import httpx
from bizzbot.schemas import ChatsResponse, ClientChat, MessageModel, PromptTopic
from bizzbot.models import Chats, Message, Summaries
from auth.db_connection import chats_collection, messages_collection, summaries_collection


# ----------------------- QUERY RAG API -----------------------
async def query_rag_api(prompt: MessageModel | list[MessageModel]) -> MessageModel:
    if isinstance(prompt, list):
        prompt_json = {"messages": [p.model_dump() for p in prompt]}
    else:
        prompt_json = {"messages": prompt.model_dump()}

    async with httpx.AsyncClient(timeout=90.0) as client:
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
async def get_chat_topic(prompt: ClientChat, user_id: str | None = None) -> PromptTopic:
    if not prompt.topic:
        # prefix = "In one word or , give a topic for conversations that may arise from this prompt: \n"
        prefix = """
        Suggest short conversation topic for this message (just one topic).

        Rules:
        - Avoid generic topics like "General", "Miscellaneous", or "Chat".
        - It should be specific to the content of the message.
        - Use simple and clear language.
        - Keep the topic under 8 words max.
        - It should not be a question.
        - Avoid overly broad or vague topics.
        - Make it engaging and relevant to the message.
        - Expand into related or deeper ideas, not just rephrasing.
        - Be diverse (cover different angles or directions).
        \n
        """
        new_prompt = MessageModel(role="user", content=prefix + prompt.content)
        topic_exists = True
        attempts = 0
        max_attempts = 10
        result = None

        while topic_exists and attempts < max_attempts:
            attempts += 1

            result = await query_rag_api(new_prompt)
            topic_existing = chats_collection.find_one({
                "user_id": ObjectId(user_id),
                "topic": result.content
                })

            if topic_existing:
                new_prompt.content += f"\nAvoid this topic: {result.content}"
            else:
                topic_exists = False
            
            print(f"Attempt {attempts}: Generated topic - {result.content}")

        return PromptTopic(
            prompt=prefix + prompt.content,
            topic=result.content
        )

    return PromptTopic(
        prompt=prompt.content,
        topic=prompt.topic
    )
    

# ----------------------- CREATE NEW CHAT -----------------------
def create_new_chat(user_id: str, topic: str, user_prompt_text: str, bot_response_text: str) -> ChatsResponse | bool:
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
        return ChatsResponse(
            id=str(chat_details.id),
            user_id=str(chat_details.user_id),
            topic=chat_details.topic,
            total_conversations=chat_details.total_conversations,
            summarised_messages=chat_details.summarised_messages,
            created_at=chat_details.created_at,
            last_updated=chat_details.last_updated
        )

    return False


# ----------------------- MODIFY CHAT TOPIC -----------------------
def edit_chat_topic(chat_id: str, topic: str) -> ChatsResponse | Literal[False]:
    #get_chat_by_id
    chat = get_chat_by_id(chat_id)

    # update chat
    if chat:
        updated_chat = chats_collection.update_one(
            {"_id": ObjectId(chat_id)},
            {
                "$set": {
                    "topic": topic,
                    "last_updated": datetime.now(timezone.utc)
                }
            },
            upsert=False
        )

    if updated_chat.modified_count == 1:
        updated_data = ChatsResponse(
            id=str(chat.id),
            user_id=str(chat.user_id),
            topic=topic,
            total_conversations=chat.total_conversations,
            summarised_messages=chat.summarised_messages,
            created_at=chat.created_at,
            last_updated=datetime.now(timezone.utc)
        )

        return updated_data

    return False


# ----------------------- INSERT EXISTING CHAT -----------------------
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


def delete_chat(id: str) -> bool:
    # delete chat if it exists
    messages_deletion = messages_collection.delete_many({"chat_id": ObjectId(id)})
    summaries_deletion = summaries_collection.delete_many({"chat_id": ObjectId(id)})
    chat_deletion = chats_collection.delete_one({"_id": ObjectId(id)})

    if chat_deletion.deleted_count == 1:
        return True

    return False

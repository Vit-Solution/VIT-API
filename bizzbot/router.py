from datetime import datetime, timezone
from typing import Annotated
from bson import ObjectId
import httpx
from fastapi import Depends, HTTPException
from fastapi import APIRouter
from auth.dependencies import get_current_user
from auth.models import Chats, Message
from bizzbot.dependencies import create_new_chat, get_chat_by_id, get_chat_topic, query_rag_api
from bizzbot.schemas import MessageModel
from config import RAG_API_URL
from bizzbot.schemas import ClientChat, MyChats


bizzbot = APIRouter(
    prefix="/api/v1/bizzbot",
    tags=["bizzbot"],
)



# ----------------------- CHAT WITH BIZZBOT -----------------------
"""
Steps to process chats going to bot:
- New chat (no chat_id):
    1. Get topic for chat from bot
    2. Query bot with prompt
    3. Store chat details (prompt and response) in DB
    4. return prompt and response to client

- Existing chat (chat_id):
    1. Get chat details from DB using chat_id
    2. Query bot with prompt and chat context (raw conversations or summarised conversations + raw recent messages)
    3. Store chat details (prompt and response) in DB
    4. return prompt and response to client

- Chat continuation
"""


@bizzbot.post("/")
async def chat_with_bizzbot(prompt: ClientChat, user_id: Annotated[str, Depends(get_current_user)]) -> list[MessageModel] | None:
    """
    ---------------------------------------------------------
    STILL IN PROGRESS ...
    ---------------------------------------------------------

    Handles chats with Bizzbot.
    * If the chat is new;
    It gets the topic from the bot, queries the bot with the prompt, stores the chat and conversation details in DB.
    
    * If the chat is existing; 
    It gets the chat details from DB, queries the bot with chat context (raw conversations or summarised conversations + raw recent messages), stores the chat and message details in DB.

    Response:
        A list of MessageModel objects containing the prompts and responses.
    """
    # --------------- NEW CHATS ---------------
    # get topic for new chats
    if len(prompt.chat_id) <= 1:
        topic = await get_chat_topic(prompt)
        topic = topic.topic

        # query bot with prompt
        bot_prompt = MessageModel(
            role="user",
            content=prompt.content
        )
        response = await query_rag_api(bot_prompt)

        # store chat and message details in db
        new_chat = create_new_chat(
            user_id=user_id,
            topic=topic,
            user_prompt_text=prompt.content,
            bot_response_text=response.content
        )

        # return prompt and response to client
        client_response = [
            MessageModel(role="user", content=prompt.content),
            MessageModel(role="assistant", content=response.content)
        ]

        return client_response
    
    # # --------------- EXISTING CHATS ---------------
    # # get chat details from db
    # chat_details = await get_chat_by_id(prompt.chat_id)

    # # query bot with prompt and chat context (raw conversations or summarised conversations + raw recent messages)
    # bot_prompt = MessageModel(
    #     role="user",
    #     content=prompt.content
    # )
    # response = await query_rag_api(bot_prompt)

    # # store chat and message details in db
    # new_chat = create_new_chat(
    #     user_id=user_id,
    #     topic=chat_details.topic,
    #     user_prompt_text=prompt.content,
    #     bot_response_text=response.content
    # )

    # # return prompt and response to client
    # client_response = [
    #     MessageModel(role="user", content=prompt.content),
    #     MessageModel(role="assistant", content=response.content)
    # ]


@bizzbot.post("/summarize-chat", deprecated=True)
async def summarize_chat(prompt: ClientChat, user_id: Annotated[str, Depends(get_current_user)]):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Forward request to external RAG API
            response = await client.post(
                RAG_API_URL,
                headers={"accept": "application/json", "Content-Type": "application/json"},
                json=prompt.model_dump()
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Upstream API error: {e}")
        
        # timmy response
        # me prompt for topic: In three words or less, give a topic for this conversation.
    
    result = response.json()
    return result


@bizzbot.get("/my-chats", deprecated=True)
async def get_user_chats(user_id: Annotated[str, Depends(get_current_user)]) -> MyChats:
    # Placeholder for fetching user chats from the database
    return {
        "user_id": user_id,
        "chats": {
            "chat1_id": "Topic 1",
            "chat2_id": "Topic 2",
        }
    }
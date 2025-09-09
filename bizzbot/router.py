from datetime import datetime, timezone
from typing import Annotated
from bson import ObjectId
from fastapi import Depends, Query
from fastapi import APIRouter
from auth.dependencies import get_current_user
from auth.db_connection import messages_collection, summaries_collection, chats_collection
from bizzbot.dependencies import create_new_chat, get_chat_by_id, get_chat_topic, insert_existing_chats, query_rag_api
from bizzbot.models import Chats, Summaries
from bizzbot.schemas import MessageModel, ChatsResponse, ClientChat
from config import RAG_API_URL


bizzbot = APIRouter(
    prefix="/api/v1/bizzbot",
    tags=["bizzbot"],
)


# ----------------------- GET USER'S CHATS -----------------------
@bizzbot.get("/my-chats")
async def get_user_chats(user_id: Annotated[str, Depends(get_current_user)]) -> list[ChatsResponse]:
    """
    Get all chats of a user.

    Args:
        user_id (str): user id

    Returns:
        list[ChatsResponse]: a list of ChatsResponse objects
    """
    user_chats = chats_collection.find({"user_id": ObjectId(user_id)})
    user_chats = [
        ChatsResponse(
            id=str(chat["_id"]),
            user_id=str(chat["user_id"]),
            topic=chat["topic"],
            total_conversations=chat["total_conversations"],
            summarised_messages=chat["summarised_messages"],
            created_at=chat["created_at"],
            last_updated=chat["last_updated"]
        ) for chat in user_chats
    ]

    return user_chats


# ----------------------- GET USER'S CONVERSATIONS -----------------------
@bizzbot.get("/my-chats/messagess/{chat_id}")
async def get_chat_messages(
    chat_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    page_size: int = Query(40, description="Page size/maximum number of results"),
    page_number: int = Query(1, description="Page number"),
    ) -> list[MessageModel]:
    """
    Get paginated messages of a chat.

    Args:
        chat_id (str): chat id
        user_id (str): user id
        page_size (int, optional): Page size/maximum number of results. Defaults to 40.
        page_number (int, optional): Page number. Defaults to 1.

    Returns:
        list[MessageModel]: a list of MessageModel objects
    """
    skip = page_size * (page_number - 1)
    messages = messages_collection.find({"chat_id": ObjectId(chat_id)}).sort("timestamp", 1).skip(skip).limit(page_size)
    messages = [MessageModel(role=message["role"], content=message["content"]) for message in messages]

    return messages


# ----------------------- CHAT WITH BIZZBOT -----------------------
@bizzbot.post("/new-chat")
async def start_new_chat(prompt: ClientChat, user_id: Annotated[str, Depends(get_current_user)]) -> list[bool | ChatsResponse | MessageModel] | None:
    """
    Handles new chats with Bizzbot.
    1. It gets the topic from the bot based on the prompt.
    2. It queries the bot with the prompt.
    3. It stores the chat and conversation details in DB.
    4. It returns the prompt and response to client.

    Response:
        A list of new chat details and MessageModel objects containing the prompt and response.
    """
    # get topic for new chats
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
        new_chat,
        MessageModel(role="user", content=prompt.content),
        MessageModel(role="assistant", content=response.content)
    ]

    return client_response


@bizzbot.post("/")
async def chat_with_bizzbot(
    prompt: ClientChat,
    user_id: Annotated[str, Depends(get_current_user)],
    # page_size: int = Query(40, description="Page size/maximum number of results"),
    # page_number: int = Query(1, description="Page number"),
    ) -> list[MessageModel] | None:
    """
    Chat with BizzBot for existing chats.

    This endpoint is used for when a user continues a conversation with BizzBot.
    It queries the bot with the summary of very long conversations (if any), the recent messages and the latest user prompt.
    It returns the last 20 prompts and responses to client (that's 40 messages).

    Request Body:
        A ClientChat object containing the prompt and chat_id.

    Response:
        A list of MessageModel objects containing the last 20 prompts and responses.
    """
    # skip = page_size * (page_number - 1)

    # --------------- EXISTING CHATS ---------------
    # retrieve all messages with chat_id: case study = 50 messages
    # 50 messages div 20 = 2 summaries + 10 recent raw messages
    total_messages_count = messages_collection.count_documents({"chat_id": ObjectId(prompt.chat_id)})
    should_have_summarised = total_messages_count//20 # 20 messages makeup 1 summary

    # get chat details from db
    chat_details = get_chat_by_id(prompt.chat_id)

    # initialised necessary variables to prevent UnboundLocalError
    summary = MessageModel(role="user", content="")
    recent_raw = []
    try:
        last_summary = summaries_collection.find(
            {"chat_id": ObjectId(prompt.chat_id)}).sort("created_at", -1).limit(1)[0]
    except IndexError:
        last_summary = None
    
    if last_summary:
        last_summary = Summaries(
            id=last_summary["_id"],
            chat_id=last_summary["chat_id"],
            summary=last_summary["summary"],
            from_msg=last_summary["from_msg"],
            to_msg=last_summary["to_msg"],
            created_at=last_summary["created_at"]
        )

    # check if chat's summary is updated
    if chat_details.summarised_messages != should_have_summarised * 20:
        last_summary_index = last_summary.to_msg if last_summary else 0

        # get unsammarised messages and summarize
        to_summarize = messages_collection.find(
            {"chat_id": ObjectId(prompt.chat_id)}).sort("timestamp", 1).skip(last_summary_index).limit(20)
        
        to_summarize = [MessageModel(role=msg["role"], content=msg["content"]) for msg in to_summarize]
        summary_prompt = MessageModel(
            role="user",
            content="Summarize the conversations above: \n\n"
            # content="\n".join([msg.content for msg in to_summarize])
        )
        to_summarize.append(summary_prompt)
        summary = await query_rag_api(to_summarize)
    else:
        # get recent raw messages
        recent_raw = messages_collection.find(
            {"chat_id": ObjectId(prompt.chat_id)}).sort("timestamp", 1).skip(should_have_summarised * 20)
        
        recent_raw = [MessageModel(
            role=msg["role"], content=msg["content"]
        ) for msg in recent_raw]

    # query bot with summary + recent raw messages + latest prompt.
    latest_bot_prompt = MessageModel(
        summary=summary.content if len(summary.content) > 0 else None,
        role="user",
        content=prompt.content
    )

    recent_raw.append(latest_bot_prompt)
    response = await query_rag_api(recent_raw)

    # -------- update chat model with details to store in db -------
    updated_chat_details = Chats(
        id=chat_details.id,
        user_id=chat_details.user_id,
        topic=chat_details.topic,
        total_conversations=chat_details.total_conversations + 1,
        summarised_messages=should_have_summarised * 20,
        created_at=chat_details.created_at,
        last_updated=datetime.now(timezone.utc)
    )

    new_summary = None
    if summary.content:
        new_summary = Summaries(
            id=ObjectId(),
            chat_id=chat_details.id,
            summary=summary.content,
            from_msg=1 if not last_summary else last_summary.to_msg + 1,
            to_msg=20 if not last_summary else last_summary.to_msg + 20,
            created_at=datetime.now(timezone.utc)
        )

    # store chat, message, response and summary details in db
    status = insert_existing_chats(
        new_prompt=prompt,
        response=response,
        updated_chat=updated_chat_details,
        summary=new_summary
    )

    # return last 20 prompts and responses to client (that's 40 messages)
    last_messages = messages_collection.find({"chat_id": ObjectId(prompt.chat_id)}).sort("timestamp", 1).skip(should_have_summarised * 20)

    client_response = [
        MessageModel(role=msg["role"], content=msg["content"]) for msg in last_messages
    ]

    if status:
        return client_response

# VIT-API

VIT-API is a FastAPI-powered backend for Bizzbot, a conversational assistant focused on business information and registration trends in Nigeria. It integrates with external RAG (Retrieval-Augmented Generation) APIs and MongoDB for chat storage and retrieval.

## Features

- **User Authentication:** Secure endpoints using JWT-based authentication.
- **Chat Management:** Create, retrieve, and summarize user chats.
- **Business Insights:** Query external APIs for business-related information.
- **MongoDB Integration:** Store chats, messages, and summaries.
- **Async API Calls:** Fast, non-blocking communication with external services.

## Technologies Used

- Python 3.13+
- FastAPI
- MongoDB (via PyMongo)
- Pydantic v2
- httpx (async HTTP client)
- Uvicorn (ASGI server)
- uv package manager

## Project Structure

```
VIT-API/
│
├── bizzbot/
│   ├── models.py         # Pydantic models for MongoDB documents
│   ├── schemas.py        # API request/response schemas
│   ├── dependencies.py   # Business logic and DB helpers
│   └── router.py         # FastAPI routes for Bizzbot
│
├── auth/
│   ├── dependencies.py   # Auth helpers
│   └── db_connection.py  # MongoDB connection setup
│
├── config.py             # Configuration (API URLs, DB settings)
├── main.py               # FastAPI app entrypoint
└── README.md             # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone https://github.com/yourusername/VIT-API.git
   cd VIT-API
   ```

2. **Install uv (global) if not already installed:**
   ```
   python -m pip install --user uv
   ```

3. **Install/sync the virtual environment/dependencies:**
   ```
   uv sync
   ```

4. **Configure environment variables:**
   - Create a `.env` file and update it with variables defined in env.txt file in the root directory.
   - Edit `config.py` with your MongoDB URI and external API URLs.

5. **Run the API server:**
   ```
   uv run uvicorn main:app --reload
   ```

## Usage

- **API Endpoints:**
  - `POST /api/v1/bizzbot/new-chat` — Start a new chat with Bizzbot.
  - `GET /api/v1/bizzbot/my-chats` — Retrieve all chats for the authenticated user.
  - `POST /api/v1/bizzbot/` — Continue an existing chat.

- **Authentication:**
  - Obtain a JWT token via the auth endpoints (see `auth/`).
  - Include the token in the `Authorization` header for protected endpoints.

## Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/bizzbot/new-chat" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
        "topic": "",
        "chat_id": "",
        "role": "user",
        "content": "How do I register a logistics company in Nigeria?"
      }'
```

## Contributing

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/fooBar`).
3. Commit your changes.
4. Push to the branch (`git push origin feature/fooBar`).
5. Open a pull request.

## License

This project is licensed under the MIT License.

## Contact

For questions or support, open an issue or contact [veenzent](odumevincent19@gmail.com).
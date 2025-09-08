from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth.auth import auth_route
from bizzbot.router import bizzbot


app = FastAPI(
        title="BizBot API",
        description="API for Business's FAQ's and Knowledge Base",
        version="1.0.0",
        contact={
            "name": "VIT Team",
        }
    )

origins = [
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_route)
app.include_router(bizzbot)



@app.get("/")
async def home():

    slide_url = "https://bizai-nigerias-ai-busine-9g44w10.gamma.site/"
    frontend_url = "https://bizai-gamma.vercel.app/"
    
    return {
        "message": "Welcome to BizBot API",
        "version": "1.0.0",
        "description": "API for Business's FAQ's and Knowledge Base",
        "Documentation": "append /docs to the base url to access the documentation",
        "insight slide url": slide_url,
        "frontend_url": frontend_url
    }


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "API is healthy"
    }


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    

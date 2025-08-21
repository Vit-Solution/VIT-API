from fastapi import FastAPI


app = FastAPI(
        title="BizBot API",
        description="API for Business's FAQ's and Knowledge Base",
        version="1.0.0",
        contact={
            "name": "VIT Team",
            # "email": ""
        }
    )


@app.get("/")
async def home():
    frontend_url = "https://preview--bizbot-naija-assist.lovable.app/"
    
    return {
        "message": "Welcome to BizBot API",
        "frontend_url": frontend_url
    }






# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    

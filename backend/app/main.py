from fastapi import FastAPI
from app.api.routes.chat import router as chat_router 

      


app = FastAPI(
    title="TravelOS API",
    description="AI-powered multi-agent travel planning backend",
    version="1.0.0",
)

app.include_router(chat_router)


@app.get("/")
def root():
    return {"message": "Welcome to the TravelOS API!",
            "status": "running"}
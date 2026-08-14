from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.chat import router as chat_router


app = FastAPI(
    title="TravelOS API",
    description="AI-powered multi-agent travel planning backend",
    version="1.0.0",
)

# =============================================
# CORS — allow frontend dev server + production
# =============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to the TravelOS API!",
        "status": "running",
        "version": "1.0.0"
    }
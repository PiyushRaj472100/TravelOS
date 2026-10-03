from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.chat import router as chat_router


app = FastAPI(
    title="TravelOS API",
    description="AI-powered multi-agent travel planning backend",
    version="1.0.0",
)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/api/analytics/status")
async def analytics_status():
    try:
        from app.analytics.analytics_connection import is_available
        from app.analytics.analytics_config import AnalyticsConfig
        return {
            "enabled": AnalyticsConfig.ANALYTICS_ENABLED,
            "configured": AnalyticsConfig.is_configured(),
            "connected": is_available(),
            "database": AnalyticsConfig.SQL_SERVER_DATABASE,
            "host": AnalyticsConfig.SQL_SERVER_HOST,
        }
    except Exception as exc:
        return {
            "enabled": False,
            "connected": False,
            "error": str(exc),
        }


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
        "https://travel-os-rho.vercel.app",
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
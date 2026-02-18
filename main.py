from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from routes.auth import router as auth_router
from routes.current_user import router as current_user_router
from routes.profile import router as profile_router
from routes.orders import router as orders_router

app = FastAPI(title="Segmento Backend")

# 🌐 CORS configuration (local + production + custom domain)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://aathidyam.in",
    "https://www.aathidyam.in",
]

# Optional: also allow frontend URL from env (safe fallback)
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url and frontend_url not in origins:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔗 API Routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(current_user_router, prefix="/user", tags=["User"])
app.include_router(profile_router, prefix="/profile", tags=["Profile"])
app.include_router(orders_router, prefix="/orders", tags=["Orders"])

# ❤️ Health check (required for Railway)
@app.get("/")
def root():
    return {"status": "Backend running successfully"}

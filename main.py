from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routes.auth import router as auth_router
from routes.current_user import router as current_user_router
from routes.profile import router as profile_router
from routes.orders import router as orders_router

app = FastAPI(title="Segmento Backend")

# ✅ CORS CONFIG (FIXED)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://www.aathidyam.in",
    "https://aathidyam.in",
    "https://*.hf.space",  # Allow any Hugging Face Space subdomain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ ROUTES (NO CHANGE)
app.include_router(auth_router)
app.include_router(current_user_router)
app.include_router(profile_router)
app.include_router(orders_router)

# ✅ ROOT CHECK
@app.get("/")
def root():
    return {"status": "Backend running successfully 🚀"}

# ✅ HEALTH CHECK (FOR DEBUGGING)
@app.get("/health")
def health():
    return {"status": "ok"}
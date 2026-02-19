from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from appwrite_client import databases
from appwrite.query import Query
from utils.jwt import create_access_token, decode_access_token
from passlib.context import CryptContext
import os, uuid

router = APIRouter(prefix="/auth", tags=["Auth"])

DATABASE_ID = os.getenv("DATABASE_ID")
USERS_COLLECTION_ID = os.getenv("USERS_COLLECTION_ID")
ORDERS_COLLECTION_ID = os.getenv("ORDERS_COLLECTION_ID")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ================= HELPERS =================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hash: str) -> bool:
    return pwd_context.verify(password, hash)

# ================= REQUEST MODELS =================

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    mobile: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    loginType: str = "user"   # "user" | "admin"

# ================= REGISTER =================

@router.post("/register")
def register_user(data: RegisterRequest):
    existing = databases.list_documents(
        DATABASE_ID,
        USERS_COLLECTION_ID,
        queries=[Query.equal("email", data.email)]
    )

    if existing["total"] > 0:
        raise HTTPException(400, "User already exists")

    if len(data.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")

    databases.create_document(
        DATABASE_ID,
        USERS_COLLECTION_ID,
        document_id=str(uuid.uuid4()),
        data={
            "name": data.name,
            "email": data.email,
            "mobile": data.mobile,
            "passwordHash": hash_password(data.password),
            "role": "user"   # default role
        }
    )

    return {"success": True}

# ================= LOGIN =================

@router.post("/login")
def login_user(data: LoginRequest):
    users = databases.list_documents(
        DATABASE_ID,
        USERS_COLLECTION_ID,
        queries=[Query.equal("email", data.email)]
    )

    if users["total"] == 0:
        raise HTTPException(404, "User not found")

    user = users["documents"][0]

    if not verify_password(data.password, user["passwordHash"]):
        raise HTTPException(401, "Invalid email or password")

    # ✅ SAFE ROLE HANDLING
    role = user.get("role") or "user"

    # 🔐 ADMIN LOGIN ENFORCEMENT
    if data.loginType == "admin" and role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Access Denied: You are not an admin"
        )

    # 🔥 ATTACH GUEST ORDERS
    guest_orders = databases.list_documents(
        DATABASE_ID,
        ORDERS_COLLECTION_ID,
        queries=[
            Query.equal("email", data.email),
            Query.equal("isGuest", True)
        ]
    )

    for order in guest_orders["documents"]:
        databases.update_document(
            DATABASE_ID,
            ORDERS_COLLECTION_ID,
            order["$id"],
            {
                "isGuest": False,
                "userId": user["$id"]
            }
        )

    # 🔑 JWT TOKEN
    token = create_access_token({
        "userId": user["$id"],
        "email": user["email"],
        "role": role
    })

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["$id"],
            "name": user["name"],
            "email": user["email"],
            "mobile": user["mobile"],
            "role": role
        }
    }

# ================= MY ORDERS =================

@router.get("/my-orders")
def get_my_orders(token: str):
    try:
        payload = decode_access_token(token)
        user_id = payload.get("userId")

        if not user_id:
            raise HTTPException(401, "Invalid token")

        orders = databases.list_documents(
            DATABASE_ID,
            ORDERS_COLLECTION_ID,
            queries=[
                Query.equal("userId", user_id),
                Query.order_desc("$createdAt")
            ]
        )

        return {"success": True, "orders": orders["documents"]}

    except Exception:
        raise HTTPException(401, "Invalid or expired token")

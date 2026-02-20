from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from appwrite_client import databases
from appwrite.query import Query
from utils.jwt import create_access_token, decode_access_token
import os, uuid

router = APIRouter(prefix="/auth", tags=["Auth"])

# ================= ENV =================

DATABASE_ID = os.getenv("DATABASE_ID")
USERS_COLLECTION_ID = os.getenv("USERS_COLLECTION_ID")
ORDERS_COLLECTION_ID = os.getenv("ORDERS_COLLECTION_ID")

# ================= MODELS =================

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    mobile: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ================= REGISTER =================

@router.post("/register")
def register_user(data: RegisterRequest):
    users = databases.list_documents(
        DATABASE_ID,
        USERS_COLLECTION_ID,
        queries=[Query.equal("email", data.email)]
    )

    if users["total"] > 0:
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
            "passwordHash": data.password,   # ⚠️ later replace with bcrypt
            "role": None                     # default user
        }
    )

    return {"success": True, "message": "User registered successfully"}


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

    # ❌ Password check
    if user.get("passwordHash") != data.password:
        raise HTTPException(401, "Invalid password")

    # ================= ROLE FIX =================
    role = user.get("role")

    # Only allow exact roles
    if role not in ["admin", "user"]:
        role = "user"

    # ================= ATTACH GUEST ORDERS =================
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
            document_id=order["$id"],
            data={
                "isGuest": False,
                "userId": user["$id"]
            }
        )

    # ================= TOKEN =================
    token = create_access_token({
        "userId": user["$id"],
        "email": user.get("email"),
        "role": role
    })

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["$id"],
            "name": user.get("name"),
            "email": user.get("email"),
            "mobile": user.get("mobile"),
            "role": role
        }
    }


# ================= MY ORDERS =================

@router.get("/my-orders")
def get_my_orders(token: str):
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

    return {
        "success": True,
        "orders": orders["documents"]
    }
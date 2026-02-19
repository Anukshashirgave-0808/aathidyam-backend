from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from appwrite_client import databases
from appwrite.query import Query
from utils.jwt import create_access_token, decode_access_token
import os, uuid

router = APIRouter(prefix="/auth", tags=["Auth"])

DATABASE_ID = os.getenv("DATABASE_ID")
USERS_COLLECTION_ID = os.getenv("USERS_COLLECTION_ID")
ORDERS_COLLECTION_ID = os.getenv("ORDERS_COLLECTION_ID")

# ================= REGISTER =================

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    mobile: str | None = None   # ✅ mobile optional


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
            "passwordHash": data.password,
            "role": None        # ✅ users default to NULL
        }
    )

    return {"success": True}


# ================= LOGIN =================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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

    if user.get("passwordHash") != data.password:
        raise HTTPException(401, "Invalid password")

    # 🔥 Attach guest orders
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

    # ✅ CRITICAL FIX
    # role NULL => user
    role = user.get("role") or "user"

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
            "mobile": user.get("mobile"),  # ✅ safe
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

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
    mobile: str
    password: str


@router.post("/register")
def register_user(data: RegisterRequest):
    email = data.email.strip().lower()

    users = databases.list_documents(
        DATABASE_ID,
        USERS_COLLECTION_ID,
        queries=[Query.equal("email", email)]
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
            "email": email,
            "mobile": data.mobile,
            "passwordHash": data.password,  # ⚠️ hash later
            "role": None                   # users default to NULL
        }
    )

    return {"success": True}


# ================= LOGIN =================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    loginType: str | None = "user"  # "user" or "admin"


@router.post("/login")
def login_user(data: LoginRequest):
    email = data.email.strip().lower()

    users = databases.list_documents(
        DATABASE_ID,
        USERS_COLLECTION_ID,
        queries=[Query.equal("email", email)]
    )

    if users["total"] == 0:
        raise HTTPException(401, "Invalid credentials")

    user = users["documents"][0]

    if user["passwordHash"] != data.password:
        raise HTTPException(401, "Invalid credentials")

    # ✅ FINAL ROLE NORMALIZATION (MOST IMPORTANT LINE)
    raw_role = user.get("role")
    role = "admin" if raw_role == "admin" else "user"

    # 🔐 BACKEND ADMIN ENFORCEMENT
    if data.loginType == "admin" and role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Access Denied: You are not an admin"
        )

    # 🔥 Attach guest orders
    guest_orders = databases.list_documents(
        DATABASE_ID,
        ORDERS_COLLECTION_ID,
        queries=[
            Query.equal("email", email),
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

    token = create_access_token({
        "userId": user["$id"],
        "email": email,
        "role": role
    })

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["$id"],
            "name": user.get("name"),
            "email": email,
            "mobile": user.get("mobile"),
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

        return {
            "success": True,
            "orders": orders["documents"]
        }

    except Exception as e:
        print("❌ MY ORDERS ERROR:", e)
        raise HTTPException(500, "Internal Server Error")

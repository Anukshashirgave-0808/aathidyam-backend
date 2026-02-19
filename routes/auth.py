from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr
from appwrite_client import databases
from appwrite.query import Query
from utils.jwt import create_access_token, decode_access_token
import os, uuid

router = APIRouter(prefix="/auth", tags=["Auth"])

DATABASE_ID = os.getenv("DATABASE_ID")
USERS_COLLECTION_ID = os.getenv("USERS_COLLECTION_ID")
ORDERS_COLLECTION_ID = os.getenv("ORDERS_COLLECTION_ID")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login_user(data: LoginRequest, response: Response):
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

    # role NULL => user
    role = user.get("role") or "user"

    token = create_access_token({
        "userId": user["$id"],
        "email": user.get("email"),
        "role": role
    })

    # 🔥 SET JWT COOKIE (THIS FIXES FAILED FETCH)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,          # 🔴 REQUIRED IN PROD
        samesite="none",      # 🔴 REQUIRED FOR VERCEL
        max_age=60 * 60 * 24,
        path="/"
    )

    return {
        "success": True,
        "user": {
            "id": user["$id"],
            "name": user.get("name"),
            "email": user.get("email"),
            "mobile": user.get("mobile"),
            "role": role
        }
    }

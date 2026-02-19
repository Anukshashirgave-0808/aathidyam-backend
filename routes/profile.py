from fastapi import APIRouter, Header, HTTPException
from jose import jwt
import os
from appwrite_client import databases
from appwrite.query import Query

router = APIRouter(prefix="/profile", tags=["Profile"])

SECRET = os.getenv("JWT_SECRET")
DATABASE_ID = os.getenv("DATABASE_ID")
USERS_COLLECTION_ID = os.getenv("USERS_COLLECTION_ID")
ORDERS_COLLECTION_ID = os.getenv("ORDERS_COLLECTION_ID")


@router.get("/")
def get_profile(
    authorization: str = Header(None),
    email: str = None,
    mobile: str = None
):
    try:
        user = None

        # 1️⃣ JWT authentication
        if authorization:
            try:
                token = authorization.split(" ")[1]
                payload = jwt.decode(token, SECRET, algorithms=["HS256"])

                # ✅ FIXED KEY
                user_id = payload["userId"]

                user = databases.get_document(
                    DATABASE_ID,
                    USERS_COLLECTION_ID,
                    user_id
                )
            except Exception as e:
                print("JWT error:", e)
                user = None

        # 2️⃣ Fallback login
        if not user and (email or mobile):
            queries = []
            if email:
                queries.append(Query.equal("email", email))
            if mobile:
                queries.append(Query.equal("mobile", mobile))

            users_resp = databases.list_documents(
                DATABASE_ID,
                USERS_COLLECTION_ID,
                queries
            )

            if users_resp["total"] > 0:
                user = users_resp["documents"][0]

        if not user:
            raise HTTPException(404, "User not found")

        # Orders
        orders_resp = databases.list_documents(
            DATABASE_ID,
            ORDERS_COLLECTION_ID,
            queries=[Query.equal("userId", user["$id"])]
        )

        orders_list = [
            {
                "id": o["$id"],
                "items": o.get("items", []),
                "total": o.get("total", 0),
                "status": o.get("status", "Pending")
            }
            for o in orders_resp["documents"]
        ]

        return {
            "success": True,
            "user": {
                "id": user["$id"],
                "name": user.get("name"),
                "email": user.get("email"),
                "mobile": user.get("mobile"),
                "role": user.get("role", "user")
            },
            "orders": orders_list
        }

    except Exception as e:
        print("PROFILE ERROR:", e)
        raise HTTPException(401, "Invalid or missing token")

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
    authorization: str = Header(None),  # Optional JWT
    email: str = None,                  # Optional fallback
    mobile: str = None                  # Optional fallback
):
    """
    Fetch logged-in user details and past orders using JWT token,
    or fallback using email/mobile query parameters.
    """
    try:
        user = None

        # 1️⃣ Try JWT token first
        if authorization:
            try:
                token = authorization.split(" ")[1]
                payload = jwt.decode(token, SECRET, algorithms=["HS256"])
                user_id = payload["user_id"]
                user = databases.get_document(
                    database_id=DATABASE_ID,
                    collection_id=USERS_COLLECTION_ID,
                    document_id=user_id
                )
            except Exception as e:
                print("JWT decoding error:", e)
                user = None

        # 2️⃣ Fallback: find by email or mobile
        if not user and (email or mobile):
            queries = []
            if email:
                queries.append(Query.equal("email", email))
            if mobile:
                queries.append(Query.equal("mobile", mobile))

            users_resp = databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=USERS_COLLECTION_ID,
                queries=queries
            )

            if users_resp.get("total", 0) > 0:
                user = users_resp["documents"][0]

        # 3️⃣ If still no user, raise error
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch past orders for this user
        try:
            orders_resp = databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=ORDERS_COLLECTION_ID,
                queries=[Query.equal("userId", user["$id"])]
            )
            orders_list = [
                {
                    "id": o["$id"],
                    "items": o.get("items", []),
                    "total": o.get("total", 0),
                    "status": o.get("status", "Pending")
                }
                for o in orders_resp.get("documents", [])
            ]
        except Exception:
            orders_list = []

        return {
            "success": True,
            "user": {
                "id": user["$id"],
                "name": user.get("name", ""),
                "email": user.get("email", ""),
                "mobile": user.get("mobile", ""),
                "role": user.get("role", "user")
            },
            "orders": orders_list
        }

    except Exception as e:
        print("PROFILE ERROR:", e)
        raise HTTPException(status_code=401, detail="Invalid or missing token")

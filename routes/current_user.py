from fastapi import APIRouter, Request, HTTPException
from appwrite_client import databases
from appwrite.query import Query
import os

router = APIRouter(prefix="/user", tags=["User"])

DATABASE_ID = os.getenv("DATABASE_ID")
USERS_COLLECTION_ID = os.getenv("USERS_COLLECTION_ID")
ORDERS_COLLECTION_ID = os.getenv("ORDERS_COLLECTION_ID")

@router.get("/current")
def current_user(request: Request):
    """
    Optional route for guest fallback using cookies
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        return {"status": "guest"}

    try:
        users = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=USERS_COLLECTION_ID,
            queries=[Query.equal("$id", user_id)]
        )
        if users.get("total", 0) == 0:
            return {"status": "guest"}

        user = users["documents"][0]

        # Fetch past orders
        try:
            orders_resp = databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=ORDERS_COLLECTION_ID,
                queries=[Query.equal("userId", user_id)]
            )
            orders_list = [
                {
                    "id": o["$id"],
                    "items": o.get("items", []),
                    "total": o.get("total", 0),
                    "status": o.get("status", "Pending")
                } for o in orders_resp.get("documents", [])
            ]
        except Exception:
            orders_list = []

        return {
            "status": "user",
            "user": {
                "id": user["$id"],
                "name": user.get("name", "User"),
                "email": user.get("email", ""),
                "mobile": user.get("mobile", ""),
                "role": user.get("role", "user")
            },
            "orders": orders_list
        }

    except Exception as e:
        print("CURRENT USER ERROR:", e)
        raise HTTPException(status_code=500, detail="Server error")

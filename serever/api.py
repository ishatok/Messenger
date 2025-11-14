from fastapi import APIRouter, HTTPException
from database import Database
import json

router = APIRouter()
db = Database()


@router.post("/register")
async def register(user_data: dict):
    username = user_data.get("username", "").strip()
    password = user_data.get("password", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")

    if db.create_user(username, password):
        return {"message": "User created successfully"}
    else:
        raise HTTPException(status_code=400, detail="Username already exists")


@router.post("/login")
async def login(user_data: dict):
    username = user_data.get("username", "").strip()
    password = user_data.get("password", "")

    user = db.get_user(username)
    if user and user['password'] == password:
        return {
            "user_id": user['id'],
            "username": user['username'],
            "message": "Login successful"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/users")
async def get_users():
    users = db.get_all_users()
    return users


@router.get("/messages/{user1_id}/{user2_id}")
async def get_messages(user1_id: int, user2_id: int):
    messages = db.get_messages(user1_id, user2_id)
    return messages


@router.post("/send_message")
async def send_message(message_data: dict):
    sender_id = message_data.get("sender_id")
    receiver_id = message_data.get("receiver_id")
    content = message_data.get("content", "").strip()

    if not sender_id or not receiver_id or not content:
        raise HTTPException(status_code=400, detail="Missing required fields")

    if db.save_message(sender_id, receiver_id, content):
        return {"message": "Message sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send message")


@router.get("/user/{user_id}")
async def get_user_info(user_id: int):
    user = db.get_user_by_id(user_id)
    if user:
        return user
    else:
        raise HTTPException(status_code=404, detail="User not found")


@router.get("/stats")
async def get_stats():
    """Получить статистику сервера"""
    stats = db.get_stats()
    return {
        "status": "running",
        "database": "connected",
        "statistics": stats
    }
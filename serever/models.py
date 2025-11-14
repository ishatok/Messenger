from pydantic import BaseModel
from typing import Optional

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class MessageSend(BaseModel):
    receiver_id: int
    content: str

class WebSocketMessage(BaseModel):
    type: str
    data: dict
from pydantic import BaseModel


class UserCreate(BaseModel):
    login: str
    password: str


class UserProfile(BaseModel):
    login: str
    avatar_irl: str | None


class MessageCreate(BaseModel):
    from_user_id = int
    to_user_id = int
    text = str


class MessageInDB(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    text: str
    timestamp: str

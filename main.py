import uvicorn
from fastapi import FastAPI
from  pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    login: str
    password: str

class MessageCreate(BaseModel):
    content: str


@app.get('/login')
def login():
    data = SignIn(login='vasya', password='12345')
    return data


if __name__ == "main":
    uvicorn.run("main:app", reload=True)
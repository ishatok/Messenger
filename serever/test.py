from fastapi import FastAPI
from fastapi.websockets import WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Разрешаем все CORS запросы
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Клиент подключился")
    try:
        while True:
            message = await websocket.receive_text()
            print(f"Получено: {message}")
    except Exception as e:
        print(f"Клиент отключился (ошибка: {e})")

@app.get("/")
def read_root():
    return {"status": "WebSocket server is running"}

# Запуск: uvicorn server:app --host 0.0.0.0 --port 8000
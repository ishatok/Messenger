from fastapi import WebSocket
from typing import Dict


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"✅ Пользователь {user_id} подключен к WebSocket")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"❌ Пользователь {user_id} отключен от WebSocket")

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
                print(f"📤 Сообщение отправлено пользователю {user_id}")
            except Exception as e:
                print(f"❌ Ошибка отправки сообщения пользователю {user_id}: {e}")
                self.disconnect(user_id)
        else:
            print(f"⚠️ Пользователь {user_id} не в сети")

    async def broadcast(self, message: str):
        disconnected_users = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except:
                disconnected_users.append(user_id)

        for user_id in disconnected_users:
            self.disconnect(user_id)


manager = ConnectionManager()
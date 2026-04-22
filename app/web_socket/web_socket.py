"""Web Socket module"""
from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """Connection manager class"""
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, device_id: str):
        """Connect to websocket"""
        await websocket.accept()
        if device_id not in self.active_connections:
            self.active_connections[device_id] = []

        self.active_connections[device_id].append(websocket)
        print(f"📱 Клієнт підключився до хаба {device_id}")

    def disconnect(self, websocket: WebSocket, device_id: str):
        """Disconnect from websocket"""
        if device_id in self.active_connections:
            if websocket in self.active_connections[device_id]:
                self.active_connections[device_id].remove(websocket)

            if not self.active_connections[device_id]:
                del self.active_connections[device_id]
        print(f"📱 Клієнт відключився від хаба {device_id}")

    async def broadcast_to_device(self, device_id: str, message: dict):
        """Broadcast message to device"""
        if device_id in self.active_connections:
            for connection in self.active_connections[device_id]:
                try:
                    await connection.send_json(message)
                except Exception: # pylint: disable=road-exception-caught
                    pass

ws_manager = ConnectionManager()

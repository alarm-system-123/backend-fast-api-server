"""Main file"""
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, WebSocketDisconnect
from starlette.websockets import WebSocket

from app.database import get_system_state_for_device, get_sensors_for_device
from app.mqtt import mqtt
from app.routers import system, schedules, sensors, events, health
from app.scheduler import start_scheduler, scheduler
from app.web_socket.web_socket import ws_manager

@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=redefined-outer-name,unused-argument
    """Lifespan context manager"""
    print("🚀 Запуск сервера...")
    await mqtt.connection()
    start_scheduler()

    yield

    print("🛑 Зупинка сервера...")
    if scheduler.running:
        scheduler.shutdown()

    if getattr(mqtt.client, "_connection", None) is not None:
        await mqtt.client.disconnect()


app = FastAPI(title="Smart Home IoT Server", lifespan=lifespan)

app.include_router(system.router)
app.include_router(sensors.router)
app.include_router(schedules.router)
app.include_router(events.router)
app.include_router(health.router)

@app.websocket("/ws/state/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """Websocket endpoint"""
    await ws_manager.connect(websocket, device_id)
    try:
        current_system_state = await get_system_state_for_device(device_id)
        current_sensors = await get_sensors_for_device(device_id)

        await websocket.send_json({
            "event": "initial_state",
            "system_state": current_system_state,
            "sensors": current_sensors
        })

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, device_id)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

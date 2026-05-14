from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.observability.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)
        logger.info("ws_connected", total=len(self.active))

    def disconnect(self, ws: WebSocket) -> None:
        self.active.remove(ws)
        logger.info("ws_disconnected", total=len(self.active))

    async def broadcast(self, message: dict) -> None:
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            action = data.get("action", "")
            if action == "ping":
                await ws.send_json({"type": "pong"})
            elif action == "subscribe":
                await ws.send_json({"type": "subscribed", "channel": data.get("channel", "all")})
            else:
                await ws.send_json({"type": "error", "message": f"Unknown action: {action}"})
    except WebSocketDisconnect:
        manager.disconnect(ws)

from fastapi import (Request, FastAPI, WebSocket)
from .proto_files import models_pb2
import base64

app = FastAPI()

# WhoAmI will be in charge of giving the player a cookie
@app.get("/whoami")
def whoami(request : Request):
    player = models_pb2.PlayerModel(name="PhotosynthesisDev", score=420)
    player_bytes = player.SerializeToString()
    player_base64 = base64.b64encode(player_bytes).decode('utf-8')
    return {"player": player_base64}

# This is going to be core websocket of maintaining player state
@app.websocket("/netraiders")
async def netraiders(websocket : WebSocket):
    await websocket.accept()
    try:
        while True:
            _ = (await websocket.receive()).get("text", "")
            iterator += 1
            await websocket.send_text(f"ACK: {iterator}")
    except Exception as e:
        try:
            await websocket.close()
        except Exception as e:
            logging.error(e)
    finally:
        ...
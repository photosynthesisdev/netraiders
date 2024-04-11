from fastapi import (Request, Response, FastAPI, WebSocket)
from .proto_files import models_pb2
import base64
import logging

app = FastAPI()

# WhoAmI will be in charge of giving the player a cookie
@app.get("/whoami")
def whoami(request : Request):
    return request.headers

@app.post("/protoUpload")
async def protoUpload(request : Request):
    body_bytes = await request.body()
    player = models_pb2.PlayerModel().FromString(body_bytes)
    response_bytes = player.SerializeToString()
    return Response(content=response_bytes, media_type="application/x-protobuf")

# This is going to be core websocket of maintaining player state
@app.websocket("/netraidersProtobuf")
async def netraidersProtobuf(websocket : WebSocket):
    await websocket.accept()
    player = models_pb2.PlayerModel(name="Basic Client", score=0)
    try:
        while True:
            await websocket.send_text(player.SerializeToString()) # Send a default model to PlayerModel - make name="Basic Client", score = 0
            inputs_bytes = await websocket.receive_bytes() # Receive PlayerInputs - if input is true, iterate player's score by +=1
            inputs = models_pb2.PlayerInputs().FromString(inputs_bytes)
            if inputs.pressed_key:
                player.score += 1
    except Exception as e:
        try:
            await websocket.close()
        except Exception as e:
            logging.error(e)
    finally:
        ...

@app.websocket("/netraidersJson")
async def netraidersJson(websocket : WebSocket):
    from .models import PlayerModel, PlayerInputs
    await websocket.accept()
    player = PlayerModel(name="Json Client", score = 0)
    try:
        while True:
            await websocket.send_text(player.json()) # Send a default model to PlayerModel - make name="Basic Client", score = 0
            input_str = (await websocket.receive()).get("text", "") # Receive PlayerInputs - if input is true, iterate player's score by +=1
            #inputs = PlayerInputs.parse_obj(json.loads(input_str))
            #if inputs.pressed_key:
            player.score += 1
    except Exception as e:
        try:
            logging.debug(e)
            await websocket.close()
        except Exception as e:
            logging.debug(e)
    finally:
        ...
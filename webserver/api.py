from fastapi import (Request, Response, FastAPI, WebSocket)
from .proto_files import models_pb2
import base64
import logging
import json

app = FastAPI()


@app.get("/whoami")
def whoami(request : Request):
    '''This endpoint will be in charge of issuing cookie to player for identifying them. Let them make persistent account, maintain leaderboard.'''
    return "I am me."

@app.websocket("/netraiderConnect")
async def netraider(websocket : WebSocket):
    from .models import NetRaiderPlayer, NetRaiderInput
    await websocket.accept()
    player = NetRaiderPlayer(user_id = 1, username = "BasicUser")
    try:
        # websocket's while true loop.
        while True:
            # send the players current 'state' to them. When game starts, this will just be default values (score is zero). 
            await websocket.send_text(player.json())
            # receive from the player their inputs (pressed WASD, space, clicked)
            raw_input_json = (await websocket.receive()).get("text", "") 
            # player inputs
            player_inputs = json.loads(raw_input_json)
            # PROCESS INPUTS
            if player_inputs['up']:
                player.y += 15
            if player_inputs['down']:
                player.y -= 15
            if player_inputs['left']:
                player.x -= 15
            if player_inputs['right']:
                player.x += 15
    except Exception as e:
        try:
            logging.error(f'WebSocket Close --- {e}')
            await websocket.close()
        except Exception as e:
            logging.error(e)
    finally:
        # any cleanup logic we need goes here (such as notifying other players of this players disconnect, closing database connection, etc.)
        logging.error(f'WebSocket Finally closed')
    

@app.websocket("/netraidersProtobuf")
async def netraidersProtobuf(websocket : WebSocket):
    '''Websocket for testing Protobuf Serialization/Deserialization speed.'''
    await websocket.accept()
    # use the protobuf that we build in proto_files folder for PlayerModel (super sipmle, just name & score)
    player = models_pb2.PlayerModel(name="Basic Client", score=0)
    try:
        # websocket's while true loop.
        while True:
            # send the players current 'state' to them. When game starts, this will just be default values (score is zero). 
            await websocket.send_text(player.SerializeToString())
            # receive from the player their inputs (pressed WASD, space, clicked)
            inputs_bytes = await websocket.receive_bytes()
            inputs = models_pb2.PlayerInputs().FromString(inputs_bytes)
            # if player was 'pressing a key' add 1 to their score. In the current unity build, this is just true by default.
            # However, in the actual game build, this is where any arbitrary logic would go where we would process the players inputs to compute their new 'state'
            if inputs.pressed_key:
                player.score += 1
    except Exception as e:
        try:
            await websocket.close()
        except Exception as e:
            logging.error(e)
    finally:
        # any cleanup logic we need goes here (such as notifying other players of this players disconnect, closing database connection, etc.)
        ...

@app.websocket("/netraidersJson")
async def netraidersJson(websocket : WebSocket):
    '''Websocket for testing JSON speed. See Protobuf socket for comments on how that works'''
    from .models import PlayerModel, PlayerInputs
    await websocket.accept()
    player = PlayerModel(name="Json Client", score = 0)
    try:
        while True:
            await websocket.send_text(player.json())
            input_str = (await websocket.receive()).get("text", "") 
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
from fastapi import (Request, Response, FastAPI, WebSocket)
from .proto_files import models_pb2
import base64
import logging
import json
import etcd3
import time

app = FastAPI()

@app.get("/whoami")
def whoami(request : Request):
    '''This endpoint will be in charge of issuing cookie to player for identifying them. Let them make persistent account, maintain leaderboard.'''
    return {"user": "BasicUser"}

@app.websocket("/netraiderConnect")
async def netraider(websocket : WebSocket):
    from .models import NetRaiderPlayer, NetRaiderInput, ServerSimulation
    await websocket.accept()
    # create a simulation object (the game room)
    simulation = ServerSimulation()
    # create our player object
    player = NetRaiderPlayer(user_id = 1, username = "BasicUser")
    # create our database connection. We use ETCD for fast reliable key value store.
    database = etcd3.client(host='localhost', port=2379)
    try:
        while True:
            now_unix = time.time()
            if now_unix > (simulation.last_time_step + (1/simulation.time_step)):
                # Read all of a user's inputs from database. 
                raw_database_tuples = database.get_prefix(f'/queued_inputs/basicuser')
                # A 'network iteration' has passed. Update player of all other players states.
                inputs = [json.loads(_tuple[0].decode()) for _tuple in raw_database_tuples]
                # sort all inputs by order they were received in
                inputs = sorted(inputs, key=lambda x: x['seq_num'])
                # Initialize movement deltas
                dx, dy = 0, 0
                # user may have many inputs. Normalize them.
                input_time_fraction = 0.1 / len(inputs) if inputs else 0
                # Process all inputs for the tick
                for player_input in inputs:
                    if player_input['up']:
                        dy += player.speed * input_time_fraction
                    if player_input['down']:
                        dy -= player.speed * input_time_fraction
                    if player_input['left']:
                        dx -= player.speed * input_time_fraction
                    if player_input['right']:
                        dx += player.speed * input_time_fraction
                player.x += dx
                player.y += dy
                simulation.last_time_step = now_unix
                # delete knowledge of inputs
                database.delete_prefix(f'/queued_inputs/basicuser')
                await websocket.send_text(player.json())
            raw_input_json = (await websocket.receive()).get("text", "")
            player_inputs = json.loads(raw_input_json)
            database.put(f'/queued_inputs/basicuser/{player_inputs.seq_num}', value=player_inputs.json())
    except Exception as e:
        try:
            logging.error(f'WebSocket Close --- {e}')
            await websocket.close()
        except Exception as e:
            logging.error(e)
    finally:
        # any cleanup logic we need goes here (such as notifying other players of this players disconnect, closing database connection, etc.)
        logging.error(f'WebSocket Finally closed')
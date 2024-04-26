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
    from .models import NetRaiderPlayer, NetraiderInput, ServerSimulation
    await websocket.accept()
    # create a simulation object (the game room)
    simulation = ServerSimulation()
    # create our player object
    player = NetRaiderPlayer(user_id = 1, username = "BasicUser")
    # create our database connection. We use ETCD for fast reliable key value store.
    database = etcd3.client(host='localhost', port=2379)
    # in order to get proper client side prediction, clients must know what their RTT is to server.
    start_time = time.time()
    await websocket.send_text("ping")
    await websocket.receive_text()
    end_time = time.time()
    # get rtt in terms of ticks
    tick_rtt = (end_time-start_time) * simulation.tick_rate
    # attach to players object
    player.tick_rtt = tick_rtt
    try:
        while True:
            await ...
            now_unix = time.time()
            if now_unix > (simulation.last_time_step + (1/simulation.tick_rate)):
                simulation.last_time_step = now_unix
                simulation.tick += 1
                users_input_for_tick = database.get(f'/queued_inputs/basicuser/{simulation.tick}')

                # Read all of a user's inputs from database and sort them.
                raw_database_tuples = list(database.get_prefix(f'/queued_inputs/basicuser'))
                inputs = [json.loads(_tuple[0].decode()) for _tuple in raw_database_tuples] if len(raw_database_tuples) > 0 else []
                inputs = sorted(inputs, key=lambda x: x.get('tick', 0), reverse=True)
                # aggregate all inputs that user sent in time step.
                aggregate_inputs = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
                for player_input in inputs:
                    for key in aggregate_inputs:
                        if player_input.get(key, False):
                            aggregate_inputs[key] += 1
                # normalize each aggregated input.
                num_inputs = len(inputs)
                if num_inputs > 0:
                    dx = (aggregate_inputs['right'] - aggregate_inputs['left']) * (player.speed / num_inputs)
                    dy = (aggregate_inputs['up'] - aggregate_inputs['down']) * (player.speed / num_inputs)
                    # Apply normalized movement
                    player.x += dx
                    player.y += dy
                simulation.last_time_step = now_unix
                # delete knowledge of inputs
                database.delete_prefix(f'/queued_inputs/basicuser')
                await websocket.send_text(player.json())
            raw_input_json = (await websocket.receive()).get("text", "")
            player_inputs = json.loads(raw_input_json)
            database.put(f'/queued_inputs/basicuser/{player_inputs["expected_tick"]}', value=raw_input_json)
            
    except Exception as e:
        try:
            logging.error(f'WebSocket Close --- {e}')
            await websocket.close()
        except Exception as e:
            logging.error(e)
    finally:
        # any cleanup logic we need goes here (such as notifying other players of this players disconnect, closing database connection, etc.)
        logging.error(f'WebSocket Finally closed')
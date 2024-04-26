from fastapi import (Request, Response, FastAPI, WebSocket)
from .proto_files import models_pb2
import base64
import logging
import json
import etcd3
import time
from .models import NetraiderPlayer, NetraiderInput, NetraidersSimulation

app = FastAPI()

@app.get("/whoami")
def whoami(request : Request):
    '''This endpoint will be in charge of issuing cookie to player for identifying them. Let them make persistent account, maintain leaderboard.'''
    return {"user": "BasicUser"}


@app.websocket("/netraiderConnect")
async def netraider(websocket : WebSocket):
    await websocket.accept()
    player = NetraiderPlayer(user_id = 1, username = "BasicUser")
    simulation = NetraidersSimulation()
    simulation.start_simulation(player)
    try:
        while True:
            rtt_start = time.time()
            logging.error("sending user")
            # send players most recent state
            await websocket.send_text(player.json())
            logging.error("sent user")
            # collect users inputs
            user_inputs = json.loads((await websocket.receive()).get("text", ""))
            logging.error(f'Got inputs: {user_inputs}')
            # takes client input and RTT and updates simulation
            simulation.handle_client_input(user_inputs)
            logging.error("handled client input")
            # set the RTT of the player and inform them of what it is.
            rtt_end = time.time()
            rtt = rtt_end - rtt_start
            player.rtt = rtt
            player.tick_rtt = rtt * simulation.tick_rate
    except Exception as e:
        try:
            await websocket.close()
        except Exception as e:
            logging.error(e)
    finally:
        logging.error(f'WebSocket Finally closed')

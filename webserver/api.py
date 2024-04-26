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
    rtt_start = time.perf_counter()
    await websocket.send_text("ping")
    await websocket.receive()
    rtt_end = time.perf_counter()
    player.tick_rtt = (rtt_end - rtt_start) * simulation.tick_rate
    try:
        while True:
            '''
            TODO: The control flow of sending/receiving in same order seems like it might be problematic.. look at this again for better control of how we are 
            sending / receiving
            '''
            rtt_start = time.perf_counter()
            # send players most recent state
            await websocket.send_text(player.json())
            # collect users inputs
            user_inputs = json.loads((await websocket.receive()).get("text", ""))       
            # takes client input and RTT and updates simulation
            simulation.handle_client_input(user_inputs)
            # rtt end.
            rtt_end = time.perf_counter()
            # set the RTT of the player and inform them of what it is.
            player.tick_rtt = (rtt_end - rtt_start) * simulation.tick_rate
    except Exception as e:
        try:
            await websocket.close()
        except Exception as e:
            logging.error(e)
    finally:
        logging.error(f'WebSocket Finally closed')

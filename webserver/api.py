from fastapi import (Request, Response, FastAPI, WebSocket)
from .proto_files import models_pb2
import base64
import logging
import json
import etcd3
import time
import random
from .netraidersimulation import *

app = FastAPI()

@app.get("/whoami")
def whoami(request : Request):
    '''This endpoint will be in charge of issuing cookie to player for identifying them. Let them make persistent account, maintain leaderboard.'''
    return {"user": "BasicUser"}


@app.websocket("/netraiderConnect")
async def netraider(websocket : WebSocket):
    def watch_new_players(watch_response):
        for event in watch_response.events:
            if isinstance(event, etcd3.events.PutEvent):
                simulation.update_player(NetraiderPlayer.parse_obj(json.loads(event.value.decode("utf-8"))))
            elif isinstance(event, etcd3.events.DeleteEvent):
                logging.error('Player logged out')

    await websocket.accept()
    user_id = random.randint(1, 100000)
    player = NetraiderPlayer(user_id = user_id, username = "BasicUser")
    simulation = NetraidersSimulation()

    watch_player_id = simulation.database.add_watch_prefix_callback(f"/connected_players", watch_new_players) #watch for notifications

    simulation.start_simulation(player)
    rtt_start = time.perf_counter()
    await websocket.send_text("ping")
    await websocket.receive()
    rtt_end = time.perf_counter()
    player.tick_rtt = (rtt_end - rtt_start) * simulation.tick_rate
    last_sent_tick = -1
    try:
        while True:
            '''
            TODO: The control flow of sending/receiving in same order seems like it might be problematic.. look at this again for better control of how we are 
            sending / receiving
            '''
            rtt_start = time.perf_counter()
            # send players most recent state
            if last_sent_tick < player.tick:
                last_sent_tick = player.tick
                await websocket.send_text((NetraiderSnapshot(
                    server_tick = simulation.server_tick,
                    local_player_id = user_id, 
                    players=simulation.players).json()
                    )
                )
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
            logging.error(e)
            await websocket.close()
        except Exception as e:
            logging.error(e)
    finally:
        simulation.database.cancel_watch(watch_id=watch_player_id)
        simulation.database.delete(f'/connected_players/{user_id}')
        logging.error(f'WebSocket Finally closed')

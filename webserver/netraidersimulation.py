from pydantic import BaseModel
import time
import asyncio
import etcd3
import json
import logging
from .models import NetraiderPlayer, NetraiderInput, TICK_RATE


class NetraidersSimulation:
    def __init__(self):
        self.tick_rate : int = TICK_RATE
        self.server_tick : int = 0
        self.database = etcd3.client(host='localhost', port=2379)
        # represents local player of this simulation
        self.local_player : NetraiderPlayer = None

    @property
    def tick_seconds(self):
        return 1 / self.tick_rate

    def start_simulation(self, connected_player : NetraiderPlayer):
        self.local_player = connected_player
        asyncio.create_task(self.start_simulation_thread())
        # NOTE: apply whatever initialization to player in rest of this function such as spawn point, inital speed, health, etc.
        # Once we make this network simulation more than one player, the players server_tick should also match whatever the current tick is of match they joined

    async def start_simulation_thread(self):
        '''Iterates the servers tick on its own thread.'''
        while True:
            await self.iterate_timestep()

    async def iterate_timestep(self):
        '''This function should be run on its own thread at the start of the simulation'''
        # wait a tick
        await asyncio.sleep(self.tick_seconds)
        self.server_tick += 1

    
    def handle_client_input(self, netraider_input):
        '''Called when input is received from client.'''
        logging.error(f"Expected: {netraider_input['expected_tick']}, Local Tick: {self.local_player.tick}, Server Tick: {self.server_tick}")
        if netraider_input['expected_tick'] <= self.local_player.tick or netraider_input['expected_tick'] > self.server_tick:
            # Player is cheating (or our code is poorly written)! Log it.
            return
        # mark the tick that this input was for
        # TODO: Accumulate ticks inbetween frames. If player sends 10 inputs in one tick, don't process input ten times but just combine all inputs and process once.
        self.local_player.tick = int(netraider_input['expected_tick'])
        # update the users 
        if netraider_input['up']:
            self.local_player.y += self.local_player.speed
        if netraider_input['down']:
            self.local_player.y -= self.local_player.speed
        if netraider_input['left']:
            self.local_player.x -= self.local_player.speed
        if netraider_input['right']:
            self.local_player.x += self.local_player.speed
        # save users input so that other players can replicate the changes.ç
        self.database.put(f"/queued_inputs/basicuser/{netraider_input['expected_tick']}", value=json.dumps(netraider_input))        
    

from pydantic import BaseModel
import time
import asyncio
import etcd3
import json
import logging

# Defines how many hertz (ticks per second) that the network simulation will run at.
# Tick should always be a positive integer.
TICK_RATE = 60

# Defines this inputs of the user. 
# This contains the tick at which they predict the server to currently be on, as well as the keys they pressed.
class NetraiderInput(BaseModel):
    expected_tick : float = 0
    up : bool
    down : bool
    left : bool
    right : bool

class NetraiderPlayer(BaseModel):
    user_id : int
    username : str
    # the most recent authoritative tick that the player is on.
    tick : int = 0
    # what the players rtt is to the server, in terms of ticks instead of seconds
    tick_rtt : int = 0
    # what is the tick rate that the player should be using in their simulation?
    tick_rate : int = TICK_RATE
    # speed of player
    speed : float = 10
    # x,y,z coordinates of player
    x : float = 0
    y : float = 0
    z : float = 0

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
        logging.error(f"TICK = {self.server_tick}")
        self.server_tick += 1

    
    def handle_client_input(self, netraider_input):
        '''Called when input is received from client.'''
        # NOTE: Where we left off. The RTT that client is getting at start is zero (b/c we don't have first rountrip yet)
        # So this will keep returning... although its not printing the error statement, so idk whats going on. 
        logging.error(f"Expected: {netraider_input['expected_tick']}, Local Tick: {self.local_player.tick}, Server Tick: {self.server_tick}")
        if netraider_input['expected_tick'] <= self.local_player.tick or netraider_input['expected_tick'] > self.server_tick:
            # Player is cheating (or our code is poorly written)! Log it.
            # Their new input can't be less than or equal to old otherwise they are trying to change old gamestate input!
            # It also can't be greater than the current server tick because clients are always behind the server in the simulation!
            return
        # mark the tick that this input was for
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
    


        




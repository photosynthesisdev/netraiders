from pydantic import BaseModel
import time
import asyncio
import etcd3
import json
import logging
from .models import NetraiderPlayer, NetraiderInput, NetraiderSnapshot, TICK_RATE


class NetraidersSimulation:
    def __init__(self):
        self.tick_rate : int = TICK_RATE
        self._server_tick : int = 0
        self.client_tick : int = 0
        self.database = etcd3.client(host='localhost', port=2379)
        # represents local player of this simulation
        self.local_player : NetraiderPlayer = None
        self.players : List[NetraiderPlayer] = []
        self.last_tick_unix : float = -1

    @property
    def tick_seconds(self):
        return 1 / self.a

    @property
    def next_tick_unix(self):
        return self.last_tick_unix + tick_seconds

    @property
    def server_tick(self):
        '''The current tick that server is on. This is the authoritative tick.'''
        return self._server_tick

    def update_player(self, player : NetraiderPlayer):
        for existing_player in self.players:
            if existing_player.user_id == player.user_id:
                self.players.remove(existing_player)
                break
        self.players.append(player)

    def remove_player(self, disconnected_user_id : int):
        for existing_player in self.players:
            if existing_player.user_id == disconnected_user_id:
                logging.error("REMOVING PLAYER FROM EXISTING")
                self.players.remove(existing_player)
                break

    def start_simulation(self, connected_player : NetraiderPlayer):
        self.local_player = connected_player
        self.database.put(f'/connected_players/{connected_player.user_id}', value = connected_player.json())
        self.simulation_task = asyncio.create_task(self.start_simulation_thread())

    async def start_simulation_thread(self):
        '''Iterates the servers tick on its own thread.'''
        while True:
            await self.iterate_timestep()

    async def iterate_timestep(self):
        '''This function should be run on its own thread at the start of the simulation'''
        # wait a tick
        await asyncio.sleep(self.tick_seconds)
        self.last_iteration_unix = time.time()
        self._server_tick += 1

    
    def handle_client_input(self, netraider_input):
        '''Called when input is received from client.'''
        logging.error(f"Expected: {int(netraider_input['expected_tick'])}, Current Client Authoritative Tick: {self.local_player.tick}, Server Tick: {self.server_tick}")
        # figure out if client is ahead of server at all - may be negative (is this wanted?)
        ticks_ahead = netraider_input['expected_tick']-self.server_tick
        self.local_player.ticks_ahead = ticks_ahead
        # log if so
        if int(netraider_input['expected_tick']) > self.server_tick:
            logging.error(f"---- CLIENT AHEAD OF SERVER BY: {ticks_ahead}")
        #elif int(netraider_input['expected_tick']) < self.server_tick:
        #    logging.error(f"---- CLIENT BEHIND SERVER BY: {ticks_ahead*-1}")
        # set the tick to players expected tick.
        self.local_player.tick = int(netraider_input['expected_tick'])
        # update the users 
        if netraider_input['up']:
            self.local_player.y += self.local_player.speed * self.tick_seconds
        if netraider_input['down']:
            self.local_player.y -= self.local_player.speed * self.tick_seconds
        if netraider_input['left']:
            self.local_player.x -= self.local_player.speed * self.tick_seconds
        if netraider_input['right']:
            self.local_player.x += self.local_player.speed * self.tick_seconds
        # save users input so that other players can replicate the changes.ç
        self.database.put(f'/connected_players/{self.local_player.user_id}', value = self.local_player.json())


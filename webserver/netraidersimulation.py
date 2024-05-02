from pydantic import BaseModel
import time
import asyncio
import etcd3
import json
import random
import logging
from typing import List
from .models import NetraiderPlayer, NetraiderInput, NetraiderSnapshot, TICK_RATE, Vector2, BitPickup, Circle


class NetraidersSimulation:
    def __init__(self):
        self.tick_rate : int = TICK_RATE
        self._server_tick : int = 0
        self.client_tick : int = 0
        self.database = etcd3.client(host='localhost', port=2379)
        # represents local player of this simulation
        self.local_player : NetraiderPlayer = None
        self.last_tick_unix : float = -1
        self.unix_start = None
        self.watch_ids = []
        # just stores deltas for player changes - this is what gets sent in snapshot
        self.player_deltas : List[NetraiderPlayer] = []
        self.spawn_pickups : List[BitPickup] = []
        # Any player IDs to despawn?
        self.despawn_players : List[int] = []
        # Any pickups to despawn?
        self.despawn_pickups : List[int] = []
        
    @property
    def tick_seconds(self):
        return 1 / self.tick_rate

    @property
    def server_tick(self):
        '''The current tick that server is on. This is the authoritative tick.'''
        return self._server_tick

    def replicate_player_updates(self, watch_response):
        '''This function listens for any updates to players in the database.'''
        for event in watch_response.events:
            if isinstance(event, etcd3.events.PutEvent):
                self.update_player(NetraiderPlayer.parse_obj(json.loads(event.value.decode("utf-8"))))
            elif isinstance(event, etcd3.events.DeleteEvent):
                exited_user_id = int(event.key.decode('utf-8').split("/")[-1])
                logging.error(f'DELETE EVENT FOR: {exited_user_id}')
                self.remove_player(exited_user_id)

    def replicate_pickup_spawns(self, watch_response):
        '''This function listens for any changes in the database in regards to Pickups Spawning/Despawning.'''
        for event in watch_response.events:
            if isinstance(event, etcd3.events.PutEvent):
                bit_pickup = BitPickup.parse_obj(json.loads(event.value.decode('utf-8')))
                self.spawn_pickups.append(bit_pickup)
            elif isinstance(event, etcd3.events.DeleteEvent):
                _id = int(event.key.decode('utf-8').split("/")[-1])
                self.despawn_pickups.append(_id)

    def get_snapshot(self) -> NetraiderSnapshot:
        player_deltas_copy = self.player_deltas[:]
        spawn_pickups_copy = self.spawn_pickups[:]
        despawn_players_copy = self.despawn_players[:]
        despawn_pickups_copy = self.despawn_pickups[:]
        self.player_deltas.clear()
        self.spawn_pickups.clear()
        self.despawn_players.clear()
        self.despawn_pickups.clear()
        return NetraiderSnapshot(
            server_tick = self.server_tick,
            local_player_id = self.local_player.user_id,
            player_deltas = player_deltas_copy,
            spawn_pickups = spawn_pickups_copy,
            despawn_players = despawn_players_copy,
            despawn_pickups = despawn_pickups_copy
        )

    def update_player(self, player : NetraiderPlayer):
        self.player_deltas.append(player)

    def remove_player(self, disconnected_user_id : int):
        self.despawn_players.append(disconnected_user_id)

    def get_all_connected_players(self) -> List[NetraiderPlayer]:
        players = []
        connected_players = self.database.get_prefix(f'/connected_players')
        for player_tuple in connected_players:
            players.append(NetraiderPlayer.parse_obj(json.loads(player_tuple[0].decode())))
        return players

    def start_simulation(self, connected_player : NetraiderPlayer):
        now = time.time()
        unix_start = now
        self.watch_ids.append(self.database.add_watch_prefix_callback(f"/connected_players", self.replicate_player_updates)) #watch for notifications
        self.watch_ids.append(self.database.add_watch_prefix_callback(f"/pickups", self.replicate_pickup_spawns))
        # if this is first player to join, make sure they mark UNIX time of when match started.
        if len(self.get_all_connected_players()) == 0:
            self.database.put(f'/startTime', value=json.dumps(now))
        else:
            # if player is joinig a match, just pull the unix start time from database.
            unix_start = float(json.loads(self.database.get('/startTime')[0].decode()))
        self.unix_start = unix_start
        # Initalize Server Tick to whatever it should be at.
        self._server_tick = int((now-unix_start)/self.tick_seconds)
        logging.error(f"Starting on server tick: {self._server_tick}, Unix Start: {unix_start}, Time Diff: {now-unix_start}")
        self.local_player = connected_player
        self.database.put(f'/connected_players/{connected_player.user_id}', value = connected_player.json())
        all_players = self.get_all_connected_players()
        self.player_deltas += all_players
        self.simulation_task = asyncio.create_task(self.start_simulation_thread())
        self.spawning_task = asyncio.create_task(self.start_spawning_thread())

    def end_simulation(self):
        '''Cleans up any resources.'''
        for watch_id in self.watch_ids:
            self.database.cancel_watch(watch_id=watch_id)
        self.database.delete(f'/connected_players/{self.local_player.user_id}')
        if len(self.get_all_connected_players()) == 0:
            self.database.delete_prefix('/pickups')
            self.database.delete('/startTime')
        self.spawning_task.cancel()
        self.simulation_task.cancel()

    async def start_spawning_thread(self):
        while True:
            await asyncio.sleep(self.tick_seconds)
            for i in range(0, 2):
                bit_pickup = BitPickup(id = random.randint(0, 2147483647), x = random.uniform(-5, 5), y = random.uniform(-5, 5))
                self.database.put(f'/pickups/{bit_pickup.id}', value=bit_pickup.json())

    async def start_simulation_thread(self):
        '''Iterates the servers tick on its own thread.'''
        while True:
            now = time.time()
            self._server_tick = int((now-self.unix_start)/self.tick_seconds)
            elapsed = time.time() - now
            if elapsed < self.tick_seconds:
                await asyncio.sleep(self.tick_seconds - elapsed)

    def custom_lerp(self, a : float, b: float, t: float):
        if t < 0:
            t = 0
        if t > 1:
            t = 1
        return a + ((b - a) * t)

    def clamp_vector_to_world_bounds(self, vector2 : Vector2):
        if vector2.x < -10:
            vector2.x = -10
        if vector2.x > 10:
            vector2.x = 10
        if vector2.y < -10:
            vector2.y = -10
        if vector2.y > 10:
            vector2.y = 10
        return vector2
    
    def handle_client_input(self, netraider_input):
        '''Called when input is received from client.'''
        #### SOME DEBUGGING JUST FOR OUR LOGS
        logging.error(f"PLAYER: {self.local_player.user_id} - Expected: {int(netraider_input['expected_tick'])}, Current Client Authoritative Tick: {self.local_player.tick}, Server Tick: {self.server_tick}")
        ticks_ahead = netraider_input['expected_tick']-self.server_tick
        if int(netraider_input['expected_tick']) > self.server_tick:
            logging.error(f"---- CLIENT AHEAD OF SERVER BY: {ticks_ahead}")
        #### ACTUAL PROCESSING OF CLIENT STATE HAPPENS HERE
        self.local_player.tick = int(netraider_input['expected_tick'])
        # Performs calculations based on user state of where they should be on the next tick.
        # If the client isn't cheating, the value this produces should be identical to what the client has already predicted
        # If this value isn't identical, then the client will be snapped back to the authoritative position that the server gave.
        current_position = Vector2(x = self.local_player.x, y = self.local_player.y)
        input_vector = Vector2(x = netraider_input['x'], y = netraider_input['y'])
        distance = Vector2.distance(current_position, input_vector)
        current_speed = self.custom_lerp(0, 1, distance/1)
        new_user_position = self.clamp_vector_to_world_bounds(Vector2.move_towards(current_position, input_vector, current_speed * self.tick_seconds))
        # Write the new position that server calculated to users state        
        self.local_player.x = round(new_user_position.x, 5)
        self.local_player.y = round(new_user_position.y, 5)
        # Store new player state in database
        self.database.put(f'/connected_players/{self.local_player.user_id}', value = self.local_player.json())
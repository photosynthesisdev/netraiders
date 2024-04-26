from pydantic import BaseModel

class NetraiderInput(BaseModel):
    expected_tick : int = 0
    up : bool
    down : bool
    left : bool
    right : bool

class NetRaiderPlayer(BaseModel):
    tick : int = 0 # what tick is this state for?
    tick_rtt : int = 0 # what is players RTT, in terms of ticks.
    user_id : int
    username : str
    speed : float = 10 # speed per second
    x : float = 0
    y : float = 0
    z : float = 0

class NetraidersSimulation:
    def __init__(self):
        # ticks should only be positive integers.
        self.tick_rate : int = 10
        self.current_tick : int = 0
        # represents the last unix timestamp of when a tick was iterated in the simulation.
        self.last_tick_unix : float = 0
        # represents all players in the simulation.
        self.local_player : NetRaiderPlayer = None

    async def start_simulation(self, connected_player : NetRaiderPlayer):
        # starts the network simulation
        self.local_player = connected_player
        while True:
            await self.iterate_timestep()

    @property
    def tick_seconds(self):
        # returns duration of a tick, in seconds.
        return 1 / self.tick_rate
    
    async def iterate_timestep(self):
        '''This function should be run on its own thread at the start of the simulation'''
        # wait a tick
        await asyncio.sleep(self.tick_seconds)
        self.current_tick += 1
    
    def handle_client_input(self, netraider_input):
        # save the users input at that tick.
        if netraider_input['up']:
            self.local_player.y += self.local_player.speed
        if netraider_input['down']:
            self.local_player.y -= self.local_player.speed
        if netraider_input['left']:
            self.local_player.x += self.local_player.speed
        if netraider_input['right']:
            self.local_player.x -= self.local_player.speed
        
        database.put(f'/queued_inputs/basicuser/{netraider_input['expected_tick']}', value=netraider_input)

        




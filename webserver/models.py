from pydantic import BaseModel

class NetRaiderInput(BaseModel):
    tick : int = 0
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

class ServerSimulation(BaseModel):
    tick_rate : int = 10
    last_time_step : float = 0
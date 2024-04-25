from pydantic import BaseModel

class NetRaiderInput(BaseModel):
    seq_num : int = 0
    up : bool
    down : bool
    left : bool
    right : bool

class NetRaiderPlayer(BaseModel):
    user_id : int
    username : str
    speed : float = 10
    x : float = 0
    y : float = 0
    z : float = 0

class ServerSimulation(BaseModel):
    time_step : int = 10 # 10 iterations per second
    last_time_step : float = 0
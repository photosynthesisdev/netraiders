from pydantic import BaseModel


class PlayerModel(BaseModel):
    name : str
    score : int

class PlayerInputs(BaseModel):
    player_name : str
    pressed_key : bool


class NetRaiderInput(BaseModel):
    up : bool
    down : bool
    left : bool
    right : bool

class NetRaiderPlayer(BaseModel):
    user_id : int
    username : str
    x : float = 0
    y : float = 0
    z : float = 0
    
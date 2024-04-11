from pydantic import BaseModel


class PlayerModel(BaseModel):
    name : str
    score : int

class PlayerInputs(BaseModel):
    player_name : str
    pressed_key : bool
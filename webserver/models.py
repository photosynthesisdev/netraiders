from pydantic import BaseModel
import time
import asyncio
import etcd3
import json
import logging
from typing import List

# Defines how many hertz (ticks per second) that the network simulation will run at.
# Tick should always be a positive integer.
TICK_RATE = 20

class NetraiderPlayer(BaseModel):
    user_id : int
    username : str
    # the most recent authoritative tick that the player is on.
    tick : int = 0
    # what the players rtt is to the server, in terms of ticks instead of seconds
    tick_rtt : float = 0
    # how many ticks ahead is the client
    ticks_ahead : int = 0
    # speed of player
    speed : float = 250
    # x,y,z coordinates of player
    x : float = 0
    y : float = 0
    z : float = 0


class NetraiderSnapshot(BaseModel):
    local_player_id : int
    # what is server's most recent known tick (keeps client in sync)
    server_tick : int
    # what is the tick rate that the player should be using in their simulation?
    tick_rate : int = TICK_RATE
    # all of our players
    players : List[NetraiderPlayer] = []

# Defines this inputs of the user. 
# This contains the tick at which they predict the server to currently be on, as well as the keys they pressed.
class NetraiderInput(BaseModel):
    expected_tick : float = 0
    up : bool
    down : bool
    left : bool
    right : bool





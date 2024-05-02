# NetRaiders

## Final Artifacts

## 👾 PLAY NOW 👾 -> https://spock.cs.colgate.edu

Netraiders is designed to be an educational tool for Computer Networks (COSC465) students. The goal is to help students see each of the 'concepts' integrated into a practical enviroment. We cover 15/18 concepts in this project.


# TODO: Include how each of these concepts was integrated into the project. 
For example, 
1) Certificates when we used TLS certs for site
2) Access Control & WAPs in game --> more players at WAP, less data is transmiited
3) Distance Vector Routing

**Direct links**

- Encoding: modulation and framing
- Encoding: bandwidth and latency
- Reliability: interference, error detection, and error correction
- Reliability: stop-and-wait automatic repeat request
- Resource allocation: multiplexing
- Resource allocation: access control

**Multiple Hops**
- Addressing: Domain Name System
- Addressing: Internet Protocol addresses
- Routing: distance vector and link state
- Routing: Internet structure and economics
- Routing/Resource allocation: content distribution networks and traffic engineering*

**End-to-End**
- Reliability: timeouts
- Reliability: sliding window automatic repeat request
- Resource allocation: exponential backoff, slow start, and fast retransmit/fast recovery
- Resource allocation: cubic and congestion avoidance
- Resource allocation: video streaming
- Security: denial-of-service attacks
- Security: man-in-the-middle attacks and certificates



### KEY TERMS
- **Network Update Loop** refers to the while True loop running in the '/netraider' websocket, which can be found in the [`api.py`](webserver/api.py#L50-L90). This is where all important player state information, such as position, scale, or score, are computed and stored. 
- **Unity Update Loop** refers to the main Unity Engine loop. This is where all visual rendering is done.

### ARCHITECTURE
- **Authoritative Simulation** is the type of multiplayer architecture in netraiders. Players simply send their keyboard and mouse inputs to the server, and the server processes the clients new state. This is done 20 times a second. This means that it is impossible for players to commit the most egregious of hacks like getting an unlimited score.
- **Tick Based Simulation** is a way of simulating a game over a network. If implemented properly, it allows for consistent time across all clients. Each game 'tick' in a tick based simulation represents a discrete update cycle where user inputs from the previous tick are processed. Our Python implementation of our Netraider simulation can be found in [`netraidersimulation.py`](webserver/netraidersimulation.py)

### SMOOTH LOCAL CLIENT VISUALS
- **Client Side Prediction** allows for smooth gameplay for the *local player*. The Unity Update loop can run at a few hundred frames a second. The Network Update Loop runs at a strict 20 frames (ticks) per second, because networks just can't transmit data that fast (especially over TCP/IP).
- **Server Reconcilliation:** sometimes, the server takes a long time to respond to a client. But because we implemetned client side prediction, our character is still smoothly moving along the screen even though the server hasn't told us of our newest authoritative state! When the server eventually responds, our client will be so far away from the state the server sent, and thus when their position is corrected, they will get snapped back in time to an older position. This makes for choppy and jittery visuals. To account for this, clients cache their "in flight' inputs. In flight inputs are inputs which the client has sent to the server, but the server has not yet sent back the players new state. Then, when the server sends us an older, out of date, authoritative state, we correct ourselves to that position, and reapply all inputs that are in flight. If the client was lying about their position, it will be corrected. If the client is telling the truth about their inputs, their prediction should be 1:1 identical to the servers call. 

### SMOOTH REMOTE CLIENT VISUALS
- **Remote Player Interpolation:** Any player other than the one local one playing the game is referred to as a 'remote player'. We can't do client side prediction with remote players. Why? Because client side prediction is dependent on knowing what inputs the player has. The local client know's what thier inputs are, but doesn't know what the inputs of other players in the world are! Client1 must wait 1/2RTT(client2 -> server) + 1/2RTT(server -> client1) in order get another update. We simply lag client inputs by one, and the interpolate between those.



GOING TO ADD MORE TO GITHUB SOON + UPDATE WEBESITE WITH 1-2 MORE PROPER THINGS!!!

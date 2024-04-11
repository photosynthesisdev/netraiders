# netraiders

## Milestone #1 Notes:
### WEBSERVER SETUP
- With the completion of Milestone 1 we have setup our basic infastructure for FAST client/server communication.
- We have setup a simple NGINX/FastAPI WebServer
- We have discarded the idea of using QUIC / WebTransport for our games networking, as these protocols are too new and have too little support to actively develop with them

### UNITY BUILD & PERFORMANCE TESTS:
- A (very basic) Unity Build is live on http://spock.cs.colgate.edu
- Static content is served from NGINX (cdn in future?)
- WebSockets connect to FastAPI backend (see /webserver/api.py script)
- The live build contains performance tests for over Websockets, comparing Protobufs to JSON
- Protobufs perform consistently better than JSON (on my wifi I consistently get ~190 msgs/second with protobufs, ~175 msg/second with json)
- We expect the performance increase from protobufs to become a lot more pronounced as our datastructures become larger in size, as json will take longer to serialize and deserialize the data

### OTHER NOTES:
- The codebase isn't super 'robust' yet, we first had to take the time to get everything configured properly (i.e. setup NGINX, setup FastAPI, setup NGINX to distribute static files and talk to FastAPI, setup Protobufs in C# and Python, get everyone on same Unity Project, build Unity to Web version, etc). We also spent a good amount of time learning about WebTransport/QUIC/HTTP/3, which wasn't in vein as its super interesting and cutting edge knowledge, but it doesn't directly apply to our new milestone 1 goals.
- It is difficult to setup Unity with Github, as the file sizes of many Unity assets are very large (excluding scripts). Gotta figure this out. 

## Next Milestone Goals:
- Design the entire repository to be educational. The repository should feel like a Networks Lab. Simple, clear to follow, and well documented. Explain everything as if the person looking at the code has never heard of NGINX, has no clue what a WebSocket is, and has no idea what Unity is.
- Have a playable gamemode that can support 8+ players at once
- Clean and crispy UI/UX
- Players fully networked to one another, compensate for lag and disconnects.
- Figure out how to link Unity code base/assets to this github (don't want to fragment codebases in different repositories)

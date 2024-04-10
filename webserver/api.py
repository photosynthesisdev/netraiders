from fastapi import (Request, FastAPI, WebSocket)

app = FastAPI()



# WhoAmI will be in charge of giving the player a cookie
@app.get("/whoami")
def whoami(request : Request):
    return "I am me."


# This is going to be core websocket of maintaining player state
@app.websocket("/netraiders")
async def netraiders(websocket : WebSocket):
    await websocket.accept()
    iterator = 0
    try:
        while True:
            _ = (await websocket.receive()).get("text", "")
            iterator += 1
            await websocket.send_text(f"ACK: {iterator}")
    except Exception as e:
        try:
            await websocket.close()
        except Exception as e:
            logging.error(e)
    finally:
        ...
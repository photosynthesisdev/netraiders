from fastapi import (Request, FastAPI)

app = FastAPI()

@app.get('/whoami')
def whoami(request : Request):
    return "I am me."
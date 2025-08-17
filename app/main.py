import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Security, Request
from fastapi.params import Depends

from app.src.config.database import create_db_and_tables, get_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code, der beim Start des Servers ausgeführt wird
    create_db_and_tables()
    print("Ready.")
    yield
    # Code, der beim Herunterfahren des Servers ausgeführt wird
    print("Done. Goodbye.")

app = FastAPI(title="Mensabuddies API",
              version="1.0.0",
              description="[API Description goes here]",
              lifespan=lifespan,
              dependencies=[
                  Depends(get_session)
              ],
              )
# app.include_router(organizations_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Security, Request
from fastapi.params import Depends

from app.src.config.database import create_db_and_tables, get_session
from app.src.routes.organization.organization import router as organization_router
from app.src.routes.location.location import router as location_router
from app.src.routes.facility.facility import router as facility_router



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
app.include_router(organization_router)
app.include_router(location_router)
app.include_router(facility_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
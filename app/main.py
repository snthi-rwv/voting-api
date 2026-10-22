from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  (registra los modelos en Base)
from app.database import Base, engine
from app.routers import candidates, votes, voters
from app.routers import candidates, voters



@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Voting API", version="1.0.0", lifespan=lifespan)

app.include_router(voters.router)
app.include_router(candidates.router)
app.include_router(votes.router)


@app.get("/", tags=["Health"])
def health():
    return {"status": "ok"}
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app import models  # noqa: F401  (registra los modelos en Base)
from app.database import Base, engine
from app.routers import auth, candidates, votes, voters
from app.security import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Voting API", version="1.1.0", lifespan=lifespan)

protected = [Depends(get_current_user)]

app.include_router(auth.router)                              # público: login
app.include_router(voters.router, dependencies=protected)    # todo protegido
app.include_router(candidates.router, dependencies=protected)  # todo protegido
app.include_router(votes.router)  # POST y GET / protegidos dentro del router; estadísticas y gráfica públicas


@app.get("/", tags=["Health"])
def health():
    return {"status": "ok"}
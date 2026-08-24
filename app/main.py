from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.base import Base
from app.database.session import engine
from app.models import transaction, user  # noqa: F401
from app.routers import auth, transactions


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Personal Expense Tracker API",
    description="Track income and expenses with JWT authentication",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(transactions.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

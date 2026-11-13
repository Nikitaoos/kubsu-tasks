import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src import models, schemas
from src.database import get_db, init_db

# Префикс, под которым приложение доступно через прокси (например /benioff).
PATH_PREFIX = os.getenv("PATH_PREFIX", "").rstrip("/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="KubSU users", lifespan=lifespan)


async def get_user_or_404(user_id: int, db: AsyncSession) -> models.User:
    user = await db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.post("/users/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = models.User(name=user.name)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@app.get("/users/", response_model=list[schemas.User])
async def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.User).order_by(models.User.id).offset(skip).limit(limit))
    return result.scalars().all()


@app.get("/users/{user_id}", response_model=schemas.User)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_user_or_404(user_id, db)


@app.patch("/users/{user_id}", response_model=schemas.User)
async def update_user(user_id: int, user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_or_404(user_id, db)
    db_user.name = user.name
    await db.commit()
    await db.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}", response_model=dict)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_or_404(user_id, db)
    await db.delete(db_user)
    await db.commit()
    return {"detail": "User deleted"}


class StripPrefixMiddleware:
    """Срезает PATH_PREFIX, если прокси передаёт путь вида /benioff/users/ без изменений."""

    def __init__(self, app, prefix: str):
        self.app = app
        self.prefix = prefix

    async def __call__(self, scope, receive, send):
        if self.prefix and scope["type"] == "http":
            path = scope["path"]
            if path == self.prefix or path.startswith(self.prefix + "/"):
                scope = dict(scope, path=path[len(self.prefix):] or "/")
        await self.app(scope, receive, send)


if PATH_PREFIX:
    app.add_middleware(StripPrefixMiddleware, prefix=PATH_PREFIX)

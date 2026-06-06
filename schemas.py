from pydantic import BaseModel
from datetime import datetime


# ---------- 用户相关 ----------
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- 文章相关 ----------
class ArticleCreate(BaseModel):
    title: str
    content: str
    summary: str | None = None
    tag_names: list[str] = []


class ArticleOut(BaseModel):
    id: int
    title: str
    content: str
    summary: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
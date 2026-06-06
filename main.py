from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import User, Article, Tag
from schemas import UserCreate, UserOut, Token, ArticleCreate, ArticleOut
from auth import hash_password, verify_password, create_access_token, get_current_user

app = FastAPI(title="博客API", version="1.0.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"message": "博客 API 运行成功！"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ==================== 用户 ====================

@app.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名或邮箱已被注册")

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


# ==================== 文章 ====================

@app.post("/articles", response_model=ArticleOut, status_code=status.HTTP_201_CREATED)
def create_article(
    article_data: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tags = []
    for tag_name in article_data.tag_names:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.flush()
        tags.append(tag)

    article = Article(
        title=article_data.title,
        content=article_data.content,
        summary=article_data.summary,
        author_id=current_user.id,
        tags=tags,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@app.get("/articles", response_model=list[ArticleOut])
def list_articles(
    page: int = 1,
    page_size: int = 10,
    tag: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Article)

    if tag:
        query = query.join(Article.tags).filter(Tag.name == tag)

    articles = (
        query.order_by(Article.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return articles


@app.get("/articles/{article_id}", response_model=ArticleOut)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


@app.put("/articles/{article_id}", response_model=ArticleOut)
def update_article(
    article_id: int,
    article_data: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    if article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能修改自己的文章")

    article.title = article_data.title
    article.content = article_data.content
    article.summary = article_data.summary

    tags = []
    for tag_name in article_data.tag_names:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    article.tags = tags

    db.commit()
    db.refresh(article)
    return article


@app.delete("/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    if article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己的文章")

    db.delete(article)
    db.commit()
    return None
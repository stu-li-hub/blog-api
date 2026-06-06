from fastapi import FastAPI

app = FastAPI(title="博客API", version="1.0.0")


@app.get("/")
def read_root():
    return {"message": "博客 API 运行成功！"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
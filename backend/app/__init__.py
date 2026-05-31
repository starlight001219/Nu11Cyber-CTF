from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Nu11Cyber CTF Platform API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.PRODUCTION else None,
    redoc_url="/redoc" if not settings.PRODUCTION else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:80", "http://43.133.171.24", "http://43.133.171.24:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"},
    )


from app.routes import auth, challenges, admin, lab, users

app.include_router(auth.router)
app.include_router(challenges.router)
app.include_router(admin.router)
app.include_router(lab.router)
app.include_router(users.router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}

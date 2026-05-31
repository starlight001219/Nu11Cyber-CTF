import re
import time
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import (
    authenticate_user,
    register_user,
    create_access_token,
    decode_token,
    get_user_by_id,
    get_user_by_username,
    is_token_blacklisted,
    blacklist_token,
)
from app.models import User
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# ==== 简易内存限流 ====
_rate_limit_store: dict[str, list[float]] = defaultdict(list)

async def rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60.0
    max_req = settings.RATE_LIMIT_PER_MINUTE
    timestamps = _rate_limit_store[client_ip]
    # 清除旧记录
    while timestamps and timestamps[0] < now - window:
        timestamps.pop(0)
    if len(timestamps) >= max_req:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    timestamps.append(now)

def sanitize_html(value: str) -> str:
    """Strip HTML tags to prevent XSS."""
    return re.sub(r'<[^>]*>', '', value) if value else value


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="无效的认证格式")
    token = authorization[7:]
    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token 已失效，请重新登录")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token 无效")
    user = await get_user_by_id(db, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


@router.post("/login")
async def login(
    req: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit),
):
    user = await authenticate_user(db, req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=token, user_id=user.id, username=user.username, role=user.role
    )


class ProfileUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    bio: str | None = None
    avatar: str | None = None


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "email": current_user.email or "",
        "score": current_user.score,
        "avatar": current_user.avatar or "",
        "bio": current_user.bio or "",
    }


@router.put("/profile")
async def update_profile(
    req: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.username is not None:
        existing = await get_user_by_username(db, req.username)
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=409, detail="用户名已被使用")
        if len(req.username) < 3:
            raise HTTPException(status_code=400, detail="用户名至少3位字符")
        current_user.username = req.username
    if req.email is not None:
        current_user.email = sanitize_html(req.email)[:120]
    if req.bio is not None:
        current_user.bio = sanitize_html(req.bio)
    if req.avatar is not None:
        if req.avatar and not req.avatar.startswith("data:image/"):
            raise HTTPException(status_code=400, detail="头像格式无效")
        current_user.avatar = req.avatar[:500000] if req.avatar else ""
    await db.commit()
    await db.refresh(current_user)
    return {
        "message": "个人资料已更新",
        "username": current_user.username,
        "avatar": current_user.avatar or "",
        "bio": current_user.bio or "",
        "email": current_user.email or "",
    }


@router.post("/register")
async def register(
    req: RegisterRequest,
    _: None = Depends(rate_limit),
    db: AsyncSession = Depends(get_db),
):
    if len(req.username) < 3 or len(req.password) < 6:
        raise HTTPException(status_code=400, detail="用户名至少3位，密码至少6位")
    existing = await get_user_by_username(db, req.username)
    if existing:
        raise HTTPException(status_code=409, detail="注册失败，请检查输入")
    safe_email = sanitize_html(req.email)[:120]
    user = await register_user(db, req.username, req.password, safe_email)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=token, user_id=user.id, username=user.username, role=user.role
    )


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/logout")
async def logout(
    authorization: str = Header(...),
    current_user: User = Depends(get_current_user),
):
    token = authorization[7:] if authorization.startswith("Bearer ") else ""
    if token:
        blacklist_token(token)
    return {"message": "已退出登录"}


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.auth_service import verify_password, hash_password

    if not verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6位")
    current_user.password_hash = hash_password(req.new_password)
    await db.commit()
    return {"message": "密码已修改"}

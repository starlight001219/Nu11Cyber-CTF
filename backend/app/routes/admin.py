from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.admin_service import get_users, update_user_role, get_stats, delete_user, get_submissions, get_all_categories
from app.services.challenge_service import create_challenge, update_challenge, delete_challenge
from app.routes.auth import get_current_user, require_admin, sanitize_html
from app.models import User

router = APIRouter(prefix="/admin", tags=["admin"])


class CreateChallengeRequest(BaseModel):
    title: str
    category: str
    difficulty: int = 1
    score: int = 100
    flag: str
    description: str
    hints: str = ""
    attachment_url: str = ""
    is_dynamic: bool = False
    max_attempts: int = 0


class UpdateChallengeRequest(BaseModel):
    title: str | None = None
    category: str | None = None
    difficulty: int | None = None
    score: int | None = None
    flag: str | None = None
    description: str | None = None
    hints: str | None = None
    is_active: bool | None = None
    max_attempts: int | None = None


class UpdateRoleRequest(BaseModel):
    user_id: int
    role: str


@router.get("/stats")
async def stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await get_stats(db)


@router.get("/users")
async def list_users(
    skip: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    users = await get_users(db, skip, limit)
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": sanitize_html(u.email or ""),
            "role": u.role,
            "score": u.score,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.put("/users/role")
async def set_role(
    req: UpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = await update_user_role(db, req.user_id, req.role)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"message": f"用户 {user.username} 角色已更新为 {req.role}"}


@router.post("/challenges")
async def add_challenge(
    req: CreateChallengeRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = req.model_dump()
    for field in ["title", "category", "description", "hints", "attachment_url"]:
        data[field] = sanitize_html(data[field])
    c = await create_challenge(db, data)
    return {"id": c.id, "title": c.title, "message": "题目已创建"}


@router.put("/challenges/{challenge_id}")
async def edit_challenge(
    challenge_id: int,
    req: UpdateChallengeRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    for field in ["title", "category", "description", "hints"]:
        if field in data:
            data[field] = sanitize_html(data[field])
    c = await update_challenge(db, challenge_id, data)
    if not c:
        raise HTTPException(status_code=404, detail="题目不存在")
    return {"message": "题目已更新"}


@router.delete("/challenges/{challenge_id}")
async def remove_challenge(
    challenge_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    ok = await delete_challenge(db, challenge_id)
    if not ok:
        raise HTTPException(status_code=404, detail="题目不存在")
    return {"message": "题目已删除"}


@router.delete("/users/{user_id}")
async def remove_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    if user_id == _.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    ok = await delete_user(db, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"message": "用户已删除"}


@router.get("/submissions")
async def list_submissions(
    skip: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    rows = await get_submissions(db, skip, limit)
    return [
        {
            "id": s.id,
            "user": username,
            "challenge": title,
            "flag_input": s.flag_input[:50],
            "is_correct": s.is_correct,
            "ip_address": s.ip_address,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        }
        for s, username, title in rows
    ]


@router.get("/categories")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await get_all_categories(db)

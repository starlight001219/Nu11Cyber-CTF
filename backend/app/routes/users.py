from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.admin_service import get_leaderboard, get_user_public_profile
from app.routes.auth import get_current_user, sanitize_html
from app.models import User

router = APIRouter(tags=["users"])


@router.get("/leaderboard")
async def leaderboard(db: AsyncSession = Depends(get_db)):
    users = await get_leaderboard(db, 100)
    return [
        {
            "rank": i + 1,
            "id": u.id,
            "username": u.username,
            "score": u.score or 0,
            "avatar": u.avatar or "",
            "role": u.role,
        }
        for i, u in enumerate(users)
    ]


@router.get("/users/{user_id}/profile")
async def user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    profile = await get_user_public_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    profile["email"] = sanitize_html(profile.get("email", ""))
    profile["bio"] = sanitize_html(profile.get("bio", ""))
    return profile

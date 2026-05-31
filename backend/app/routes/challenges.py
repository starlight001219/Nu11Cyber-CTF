from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.challenge_service import (
    get_challenges,
    get_challenge,
    submit_flag,
    get_solved_challenge_ids,
)
from app.routes.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/challenges", tags=["challenges"])


class FlagSubmit(BaseModel):
    challenge_id: int
    flag: str


@router.get("")
async def list_challenges(
    skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)
):
    challenges = await get_challenges(db, skip, limit)
    return [
        {
            "id": c.id,
            "title": c.title,
            "category": c.category,
            "difficulty": c.difficulty,
            "score": c.score,
            "solves": c.solves_count,
            "max_attempts": c.max_attempts,
        }
        for c in challenges
    ]


@router.get("/{challenge_id}")
async def challenge_detail(
    challenge_id: int, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = await get_challenge(db, challenge_id)
    if not c or not c.is_active:
        raise HTTPException(status_code=404, detail="题目不存在")
    return {
        "id": c.id,
        "title": c.title,
        "category": c.category,
        "difficulty": c.difficulty,
        "score": c.score,
        "description": c.description,
        "hints": c.hints,
        "attachment_url": c.attachment_url,
        "solves": c.solves_count,
        "max_attempts": c.max_attempts,
    }


@router.post("/submit")
async def submit_flag_endpoint(
    req: FlagSubmit,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await submit_flag(
        db, current_user.id, req.challenge_id, req.flag, request.client.host or ""
    )
    return result

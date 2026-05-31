from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.lab_service import create_lab, stop_lab, get_user_labs, get_lab_by_id
from app.routes.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/lab", tags=["lab"])


class StartLabRequest(BaseModel):
    challenge_id: int


@router.post("/start")
async def start_lab(
    req: StartLabRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lab = await create_lab(db, current_user.id, req.challenge_id)
    if not lab:
        raise HTTPException(status_code=400, detail="无法创建靶机实例（已达上限或题目不存在）")
    return {"lab_id": lab.id, "status": lab.status, "message": "靶机启动中"}


@router.post("/{lab_id}/stop")
async def stop_lab_endpoint(
    lab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await stop_lab(db, lab_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="靶机实例不存在")
    return {"message": "靶机已停止"}


@router.get("/list")
async def list_labs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    labs = await get_user_labs(db, current_user.id)
    return [
        {
            "id": l.id,
            "challenge_id": l.challenge_id,
            "container_id": l.container_id,
            "host_port": l.host_port,
            "status": l.status,
            "created_at": l.created_at.isoformat() if l.created_at else None,
            "expires_at": l.expires_at.isoformat() if l.expires_at else None,
        }
        for l in labs
    ]


@router.get("/{lab_id}")
async def lab_status(
    lab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lab = await get_lab_by_id(db, lab_id)
    if not lab or lab.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="靶机实例不存在")
    return {
        "id": lab.id,
        "challenge_id": lab.challenge_id,
        "container_id": lab.container_id,
        "host_port": lab.host_port,
        "status": lab.status,
        "created_at": lab.created_at.isoformat() if lab.created_at else None,
        "expires_at": lab.expires_at.isoformat() if lab.expires_at else None,
    }

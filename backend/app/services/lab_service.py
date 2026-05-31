import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import LabInstance, Challenge
from app.config import settings


async def create_lab(db: AsyncSession, user_id: int, challenge_id: int) -> LabInstance | None:
    challenge = await db.get(Challenge, challenge_id)
    if not challenge or not challenge.is_active:
        return None

    result = await db.execute(
        select(func.count(LabInstance.id)).where(
            LabInstance.user_id == user_id,
            LabInstance.status.in_(["running", "starting"]),
        )
    )
    active_count = result.scalar()
    if active_count >= settings.MAX_CONCURRENT_LABS:
        return None

    existing = await db.execute(
        select(LabInstance).where(
            LabInstance.user_id == user_id,
            LabInstance.challenge_id == challenge_id,
            LabInstance.status == "running",
        )
    )
    if existing.scalar_one_or_none():
        return None

    lab = LabInstance(
        user_id=user_id,
        challenge_id=challenge_id,
        status="starting",
        expires_at=datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(seconds=settings.LAB_CONTAINER_TIMEOUT),
    )
    db.add(lab)
    await db.commit()
    await db.refresh(lab)
    return lab


async def stop_lab(db: AsyncSession, lab_id: int, user_id: int) -> bool:
    lab = await db.get(LabInstance, lab_id)
    if not lab or lab.user_id != user_id:
        return False
    lab.status = "stopped"
    lab.container_id = ""
    lab.host_port = 0
    await db.commit()
    return True


async def get_user_labs(db: AsyncSession, user_id: int) -> list[LabInstance]:
    result = await db.execute(
        select(LabInstance).where(LabInstance.user_id == user_id).order_by(LabInstance.created_at.desc())
    )
    return list(result.scalars().all())


async def get_lab_by_id(db: AsyncSession, lab_id: int) -> LabInstance | None:
    return await db.get(LabInstance, lab_id)


async def update_lab_container(
    db: AsyncSession, lab_id: int, container_id: str, host_port: int
) -> bool:
    lab = await db.get(LabInstance, lab_id)
    if not lab:
        return False
    lab.container_id = container_id
    lab.host_port = host_port
    lab.status = "running"
    await db.commit()
    return True


async def cleanup_expired_labs(db: AsyncSession) -> int:
    now = datetime.datetime.now(datetime.timezone.utc)
    result = await db.execute(
        select(LabInstance).where(
            LabInstance.expires_at < now,
            LabInstance.status.in_(["running", "starting"]),
        )
    )
    expired = list(result.scalars().all())
    for lab in expired:
        lab.status = "expired"
    await db.commit()
    return len(expired)


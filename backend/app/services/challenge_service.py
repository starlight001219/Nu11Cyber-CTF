import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models import Challenge, Solve, Submission, User


async def get_challenges(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[Challenge]:
    result = await db.execute(
        select(Challenge).where(Challenge.is_active == True).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_challenge(db: AsyncSession, challenge_id: int) -> Challenge | None:
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    return result.scalar_one_or_none()


async def get_challenge_by_id(db: AsyncSession, challenge_id: int) -> Challenge | None:
    return await get_challenge(db, challenge_id)


async def submit_flag(
    db: AsyncSession, user_id: int, challenge_id: int, flag_input: str, ip: str = ""
) -> dict:
    challenge = await get_challenge(db, challenge_id)
    if not challenge:
        return {"correct": False, "message": "题目不存在"}

    if challenge.max_attempts is not None and challenge.max_attempts > 0:
        result = await db.execute(
            select(func.count(Submission.id)).where(
                Submission.user_id == user_id,
                Submission.challenge_id == challenge_id,
            )
        )
        attempts = result.scalar()
        if attempts >= challenge.max_attempts:
            return {"correct": False, "message": "已达最大尝试次数"}

    already_solved = False
    result = await db.execute(
        select(Solve).where(
            Solve.user_id == user_id,
            Solve.challenge_id == challenge_id,
        )
    )
    already_solved = result.scalar_one_or_none() is not None

    correct = flag_input.strip() == challenge.flag.strip()

    sub = Submission(
        user_id=user_id,
        challenge_id=challenge_id,
        flag_input=flag_input,
        is_correct=correct,
        ip_address=ip,
    )
    db.add(sub)

    if correct and not already_solved:
        solve = Solve(
            user_id=user_id,
            challenge_id=challenge_id,
            score_awarded=challenge.score,
        )
        db.add(solve)
        challenge.solves_count = (challenge.solves_count or 0) + 1

        user = await db.get(User, user_id)
        if user:
            user.score = (user.score or 0) + challenge.score

    await db.commit()

    if correct:
        if already_solved:
            return {"correct": True, "message": "Flag 正确（但你已提交过）"}
        return {"correct": True, "message": "Flag 正确！"}
    return {"correct": False, "message": "Flag 错误"}


async def create_challenge(db: AsyncSession, data: dict) -> Challenge:
    challenge = Challenge(**data)
    db.add(challenge)
    await db.commit()
    await db.refresh(challenge)
    return challenge


async def update_challenge(db: AsyncSession, challenge_id: int, data: dict) -> Challenge | None:
    challenge = await get_challenge(db, challenge_id)
    if not challenge:
        return None
    for key, value in data.items():
        if hasattr(challenge, key):
            setattr(challenge, key, value)
    await db.commit()
    await db.refresh(challenge)
    return challenge


async def delete_challenge(db: AsyncSession, challenge_id: int) -> bool:
    challenge = await get_challenge(db, challenge_id)
    if not challenge:
        return False
    await db.delete(challenge)
    await db.commit()
    return True


async def get_solved_challenge_ids(db: AsyncSession, user_id: int) -> set[int]:
    result = await db.execute(
        select(Solve.challenge_id).where(Solve.user_id == user_id)
    )
    return {row[0] for row in result.all()}

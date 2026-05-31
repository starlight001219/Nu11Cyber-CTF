from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Challenge, Solve, Submission


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_user_role(db: AsyncSession, user_id: int, role: str) -> User | None:
    user = await db.get(User, user_id)
    if not user:
        return None
    user.role = role
    await db.commit()
    await db.refresh(user)
    return user


async def get_stats(db: AsyncSession) -> dict:
    user_count = await db.scalar(select(func.count(User.id)))
    challenge_count = await db.scalar(select(func.count(Challenge.id)))
    solve_count = await db.scalar(select(func.count(Solve.id)))
    submission_count = await db.scalar(select(func.count(Submission.id)))

    return {
        "users": user_count or 0,
        "challenges": challenge_count or 0,
        "solves": solve_count or 0,
        "submissions": submission_count or 0,
    }


async def bulk_import_challenges(db: AsyncSession, challenges_data: list[dict]) -> list[Challenge]:
    created = []
    for data in challenges_data:
        challenge = Challenge(**data)
        db.add(challenge)
        created.append(challenge)
    await db.commit()
    for c in created:
        await db.refresh(c)
    return created


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    user = await db.get(User, user_id)
    if not user:
        return False
    await db.execute(delete(Solve).where(Solve.user_id == user_id))
    await db.execute(delete(Submission).where(Submission.user_id == user_id))
    await db.delete(user)
    await db.commit()
    return True


async def get_submissions(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[tuple]:
    result = await db.execute(
        select(Submission, User.username, Challenge.title)
        .join(User, Submission.user_id == User.id)
        .join(Challenge, Submission.challenge_id == Challenge.id)
        .order_by(Submission.submitted_at.desc())
        .offset(skip).limit(limit)
    )
    return result.all()


async def get_all_categories(db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(Challenge.category).distinct().order_by(Challenge.category)
    )
    return [row[0] for row in result.all()]


async def get_leaderboard(db: AsyncSession, limit: int = 50) -> list[User]:
    result = await db.execute(
        select(User).order_by(User.score.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_user_public_profile(db: AsyncSession, user_id: int) -> dict | None:
    user = await db.get(User, user_id)
    if not user:
        return None
    solved_result = await db.execute(
        select(Challenge.title, Challenge.category, Challenge.score, Solve.solved_at, Solve.score_awarded)
        .join(Solve, Solve.challenge_id == Challenge.id)
        .where(Solve.user_id == user_id)
        .order_by(Solve.solved_at.desc())
    )
    solves = [
        {
            "title": row[0],
            "category": row[1],
            "score": row[2],
            "solved_at": row[3].isoformat() if row[3] else None,
            "score_awarded": row[4],
        }
        for row in solved_result.all()
    ]
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "score": user.score,
        "avatar": user.avatar or "",
        "bio": user.bio or "",
        "email": user.email or "",
        "solved_count": len(solves),
        "solved_challenges": solves,
    }

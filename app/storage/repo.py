"""Best-effort repository helpers. DB failures never break a request (logged, swallowed)."""

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.observability.logging import log_event
from app.storage.db import get_sessionmaker
from app.storage.models import ApiKey, Thread, User


async def ensure_user(address: str) -> None:
    sm = get_sessionmaker()
    if not sm:
        return
    try:
        async with sm() as session:
            await session.execute(
                pg_insert(User).values(address=address).on_conflict_do_nothing(index_elements=["address"])
            )
            await session.commit()
    except Exception as e:  # noqa: BLE001
        log_event("repo_error", op="ensure_user", error=str(e))


async def is_valid_api_key(key: str) -> bool:
    sm = get_sessionmaker()
    if not sm:
        return False
    try:
        async with sm() as session:
            row = (
                await session.execute(select(ApiKey.id).where(ApiKey.key == key, ApiKey.active.is_(True)))
            ).first()
            return row is not None
    except Exception as e:  # noqa: BLE001
        log_event("repo_error", op="is_valid_api_key", error=str(e))
        return False


async def touch_thread(thread_id: str, user_id: str) -> None:
    sm = get_sessionmaker()
    if not sm:
        return
    try:
        async with sm() as session:
            await session.execute(
                pg_insert(Thread)
                .values(thread_id=thread_id, user_id=user_id)
                .on_conflict_do_update(index_elements=["thread_id"], set_={"last_used": func.now()})
            )
            await session.commit()
    except Exception as e:  # noqa: BLE001
        log_event("repo_error", op="touch_thread", error=str(e))

from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import settings

from .models import Base, User

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(self, telegram_id: int) -> User:
        user = User(telegram_id=telegram_id)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_or_create(self, telegram_id: int) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = await self.create(telegram_id)
        return user

    async def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_users_for_daily_notification(self, hour: int, minute: int) -> list[User]:
        result = await self.session.execute(
            select(User).where(
                User.daily_enabled == True,
                User.daily_hour == hour,
                User.daily_minute == minute,
            )
        )
        return list(result.scalars().all())

    async def get_users_for_alert(self) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.alert_enabled == True)
        )
        return list(result.scalars().all())

    async def update_last_aqi_level(self, telegram_id: int, level: str) -> None:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.last_aqi_level = level
            await self.session.commit()

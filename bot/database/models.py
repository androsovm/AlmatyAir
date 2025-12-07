from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)

    # Daily notifications settings
    daily_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_hour: Mapped[int] = mapped_column(Integer, default=8)
    daily_minute: Mapped[int] = mapped_column(Integer, default=0)

    # Alert notifications settings
    alert_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_threshold: Mapped[int] = mapped_column(Integer, default=101)

    # For tracking AQI changes
    last_aqi_level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<User(telegram_id={self.telegram_id})>"

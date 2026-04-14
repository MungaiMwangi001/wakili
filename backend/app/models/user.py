"""User model."""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, event
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    preferred_language: Mapped[str] = mapped_column(String(5), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


# Add event listeners to automatically normalize email
@event.listens_for(User, 'before_insert')
@event.listens_for(User, 'before_update')
def normalize_email(mapper, connection, target):
    """Automatically normalize email to lowercase before saving."""
    if target.email:
        target.email = target.email.strip().lower()
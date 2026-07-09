"""User account model."""

from enum import Enum as PyEnum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(str, PyEnum):
    ADMIN = "admin"
    CUSTOMER = "customer"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A registered account, either a customer or an admin."""

    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
    Enum(
        UserRole,
        values_callable=lambda enum: [e.value for e in enum],
        native_enum=False,
        name="user_role",
    ),
    default=UserRole.CUSTOMER,
    nullable=False,
)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    cart: Mapped["Cart | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    wishlist_items: Mapped[list["Wishlist"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

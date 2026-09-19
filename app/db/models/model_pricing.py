from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ModelPricing(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "model_pricing"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "model",
            "effective_from",
            name="provider_model_effective_from",
        ),
        CheckConstraint(
            "input_cost_per_1m_tokens >= 0",
            name="non_negative_input_cost",
        ),
        CheckConstraint(
            "output_cost_per_1m_tokens >= 0",
            name="non_negative_output_cost",
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="valid_effective_period",
        ),
        Index(
            "ix_model_pricing_lookup",
            "provider",
            "model",
            "effective_from",
        ),
    )

    provider: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    input_cost_per_1m_tokens: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
    )
    output_cost_per_1m_tokens: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
    )
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    effective_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

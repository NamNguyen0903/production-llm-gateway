from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LlmRequestAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "llm_request_attempts"
    __table_args__ = (
        UniqueConstraint(
            "llm_request_id",
            "attempt_number",
            name="request_attempt_number",
        ),
        CheckConstraint(
            "attempt_number > 0",
            name="positive_attempt_number",
        ),
        CheckConstraint(
            "status IN ('succeeded', 'failed', 'timeout', 'rate_limited')",
            name="status_allowed",
        ),
        CheckConstraint(
            "input_tokens >= 0",
            name="non_negative_input_tokens",
        ),
        CheckConstraint(
            "output_tokens >= 0",
            name="non_negative_output_tokens",
        ),
        CheckConstraint(
            "estimated_cost_usd >= 0",
            name="non_negative_cost",
        ),
        CheckConstraint(
            "latency_ms >= 0",
            name="non_negative_latency",
        ),
        Index(
            "ix_llm_request_attempts_provider_status",
            "provider",
            "status",
        ),
    )

    llm_request_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("llm_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    http_status: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    input_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    output_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    estimated_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    error_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LlmRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "llm_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('succeeded', 'failed')",
            name="status_allowed",
        ),
        CheckConstraint(
            "cache_status IN ('hit', 'miss', 'bypass')",
            name="cache_status_allowed",
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
            "total_tokens >= 0",
            name="non_negative_total_tokens",
        ),
        CheckConstraint(
            "estimated_cost_usd >= 0",
            name="non_negative_cost",
        ),
        CheckConstraint(
            "latency_ms >= 0",
            name="non_negative_latency",
        ),
        Index("ix_llm_requests_created_at", "created_at"),
        Index("ix_llm_requests_status", "status"),
    )

    request_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )
    client_request_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    api_key_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    requested_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    resolved_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    final_provider: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    cache_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="bypass",
        server_default=text("'bypass'"),
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
    total_tokens: Mapped[int] = mapped_column(
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

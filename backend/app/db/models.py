from datetime import datetime
from sqlalchemy import String, DateTime, Float, Boolean, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RequestLog(Base):
    __tablename__ = "request_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user_id: Mapped[str] = mapped_column(String(128), index=True)
    input_preview: Mapped[str] = mapped_column(Text)
    response_preview: Mapped[str | None] = mapped_column(Text, nullable=True)

    task_type: Mapped[str] = mapped_column(String(64))
    priority: Mapped[str] = mapped_column(String(64))
    privacy: Mapped[str] = mapped_column(String(64))

    selected_model: Mapped[str] = mapped_column(String(128))
    selected_provider: Mapped[str] = mapped_column(String(64))
    routing_reason: Mapped[str] = mapped_column(Text)

    latency_ms: Mapped[int] = mapped_column(Integer)
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    estimated_cost_usd: Mapped[float] = mapped_column(Float)

    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False)
    prompt_injection_risk: Mapped[str] = mapped_column(String(32), default="low")
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    fallback_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    trace_id: Mapped[str] = mapped_column(String(128))

    rag_used: Mapped[bool] = mapped_column(Boolean, default=False)
    rag_document: Mapped[str | None] = mapped_column(String, nullable=True)
    rag_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    rag_chunks: Mapped[int] = mapped_column(Integer, default=0)
    rag_top_score: Mapped[float | None] = mapped_column(Float, nullable=True)

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(256), default="New conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
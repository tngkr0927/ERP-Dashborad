"""
ERP 데이터 모델 정의.

JSONB 타입을 사용하여 비정형 데이터를 유연하게 저장합니다.
새로운 데이터 소스가 추가되더라도 스키마 변경 없이 payload에 저장할 수 있습니다.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RawDataLog(Base):
    """ERP에서 넘어오는 원본 데이터를 통째로 저장하는 테이블."""

    __tablename__ = "raw_data_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    source_system: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)


class AnalysisResult(Base):
    """분석 로직을 거친 결과를 저장하는 테이블."""

    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    analysis_type: Mapped[str] = mapped_column(String(100), nullable=False)
    result_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

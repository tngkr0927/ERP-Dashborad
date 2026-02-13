"""
ERP 데이터 모델 정의.

- RawDataLog: 업로드된 엑셀/CSV 원본 데이터를 JSONB로 저장.
- AnalysisResult: Gemini AI 분석 결과를 저장. (부모 삭제 시 CASCADE 자동 삭제)
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RawDataLog(Base):
    """업로드된 파일의 원본 데이터를 저장하는 부모 테이블."""

    __tablename__ = "raw_data_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 관계 설정: 부모 삭제 시 자식도 함께 삭제
    analyses: Mapped[list["AnalysisResult"]] = relationship(
        back_populates="raw_data", cascade="all, delete-orphan", passive_deletes=True
    )


class AnalysisResult(Base):
    """Gemini AI 분석 결과를 저장하는 자식 테이블."""

    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    raw_data_id: Mapped[int] = mapped_column(
        ForeignKey("raw_data_logs.id", ondelete="CASCADE"), nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    chart_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 역참조
    raw_data: Mapped["RawDataLog"] = relationship(back_populates="analyses")

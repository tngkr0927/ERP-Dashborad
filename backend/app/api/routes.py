"""
API 라우터 정의.

엔드포인트:
  POST /api/upload    - Raw JSON 데이터를 업로드하여 raw_data_logs에 저장.
  POST /api/analyze   - 저장된 데이터를 불러와 분석 실행 후 결과 저장.
  GET  /api/dashboard - 최신 분석 결과를 프론트엔드에 전달.
"""

from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.erp import AnalysisResult, RawDataLog
from app.services.analyzer import get_analyzer

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class UploadRequest(BaseModel):
    source_system: str
    payload: dict[str, Any]


class UploadResponse(BaseModel):
    id: int
    message: str


class AnalyzeRequest(BaseModel):
    analysis_type: str = "dummy"
    source_system: str | None = None  # None이면 전체 데이터 대상


class AnalyzeResponse(BaseModel):
    id: int
    analysis_type: str
    result_data: dict[str, Any]


class DashboardResponse(BaseModel):
    results: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=UploadResponse)
async def upload_data(body: UploadRequest, db: AsyncSession = Depends(get_db)):
    """Raw JSON 데이터를 업로드하여 raw_data_logs 테이블에 저장합니다."""
    record = RawDataLog(
        source_system=body.source_system,
        payload=body.payload,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return UploadResponse(id=record.id, message="Data uploaded successfully.")


@router.post("/analyze", response_model=AnalyzeResponse)
async def run_analysis(body: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """저장된 raw 데이터를 불러와 분석을 실행하고 결과를 저장합니다."""
    # 1. 분석기 조회
    try:
        analyzer = get_analyzer(body.analysis_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. 데이터 로드
    stmt = select(RawDataLog)
    if body.source_system:
        stmt = stmt.where(RawDataLog.source_system == body.source_system)

    rows = (await db.execute(stmt)).scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No raw data found.")

    # 3. DataFrame 변환 후 분석 실행
    df = pd.DataFrame([row.payload for row in rows])
    result = analyzer.analyze(df)

    # 4. 결과 저장
    analysis = AnalysisResult(
        analysis_type=body.analysis_type,
        result_data=result,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    return AnalyzeResponse(
        id=analysis.id,
        analysis_type=analysis.analysis_type,
        result_data=analysis.result_data,
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """최신 분석 결과를 프론트엔드에 전달합니다."""
    stmt = (
        select(AnalysisResult)
        .order_by(AnalysisResult.analyzed_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return DashboardResponse(
        results=[
            {
                "id": r.id,
                "analyzed_at": r.analyzed_at.isoformat(),
                "analysis_type": r.analysis_type,
                "result_data": r.result_data,
            }
            for r in rows
        ]
    )

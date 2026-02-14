"""
API 라우터 정의.

엔드포인트:
  POST /api/upload       - 엑셀/CSV 파일을 업로드하여 raw_data_logs에 저장.
  GET  /api/raw-data     - 저장된 원본 데이터 목록 조회 (기간 필터 지원).
  DELETE /api/raw-data/{id} - 원본 데이터 및 연결된 분석 결과 삭제.
  POST /api/analyze      - Gemini AI를 이용한 데이터 분석 실행 및 결과 저장.
  GET  /api/dashboard    - 최신 분석 결과를 프론트엔드에 전달.
"""

import io
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select, delete, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.erp import AnalysisResult, RawDataLog

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    id: int
    filename: str
    message: str


class RawDataItem(BaseModel):
    id: int
    filename: str
    created_at: str
    row_count: int
    has_analysis: bool


class RawDataListResponse(BaseModel):
    items: list[RawDataItem]
    total: int


class AnalyzeRequest(BaseModel):
    raw_data_id: int
    user_prompt: str = ""


class AnalyzeResponse(BaseModel):
    id: int
    raw_data_id: int
    summary: str
    chart_data: list[dict[str, Any]]


class DashboardResponse(BaseModel):
    results: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# POST /api/upload — 엑셀/CSV 파일 업로드
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """엑셀/CSV 파일을 업로드하여 Pandas로 파싱 후 raw_data_logs에 저장합니다."""
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    contents = await file.read()

    try:
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(contents))
        elif ext in ("xls", "xlsx"):
            df = pd.read_excel(io.BytesIO(contents), engine="openpyxl")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 파일 형식입니다: .{ext} (csv, xlsx만 지원)",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일 파싱 실패: {str(e)}")

    # NaN → None 변환 후 records 형식으로 변환
    df = df.where(df.notna(), None)
    # numpy/pandas 타입 → Python 네이티브 타입 변환 (JSONB 직렬화 호환)
    payload = json.loads(df.to_json(orient="records", force_ascii=False))

    record = RawDataLog(filename=filename, payload=payload)
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return UploadResponse(
        id=record.id,
        filename=record.filename,
        message=f"{len(payload)}건의 데이터가 업로드되었습니다.",
    )


# ---------------------------------------------------------------------------
# GET /api/raw-data — 원본 데이터 목록 조회
# ---------------------------------------------------------------------------

@router.get("/raw-data", response_model=RawDataListResponse)
async def list_raw_data(
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """저장된 원본 데이터 목록을 조회합니다. 기간 필터를 지원합니다."""
    stmt = (
        select(RawDataLog)
        .options(selectinload(RawDataLog.analyses))
        .order_by(RawDataLog.created_at.desc())
    )

    # 기본값: 최근 30일
    if start_date:
        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    else:
        start = datetime.now(timezone.utc) - timedelta(days=30)

    if end_date:
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
    else:
        end = datetime.now(timezone.utc)

    # 종료일은 해당 일자의 끝까지 포함
    end = end.replace(hour=23, minute=59, second=59)

    stmt = stmt.where(RawDataLog.created_at >= start, RawDataLog.created_at <= end)

    rows = (await db.execute(stmt)).scalars().all()

    items = [
        RawDataItem(
            id=r.id,
            filename=r.filename,
            created_at=r.created_at.isoformat(),
            row_count=len(r.payload) if isinstance(r.payload, list) else 0,
            has_analysis=len(r.analyses) > 0,
        )
        for r in rows
    ]

    return RawDataListResponse(items=items, total=len(items))


# ---------------------------------------------------------------------------
# DELETE /api/raw-data/{id} — 원본 데이터 삭제 (CASCADE로 분석 결과도 함께 삭제)
# ---------------------------------------------------------------------------

@router.delete("/raw-data/{data_id}")
async def delete_raw_data(data_id: int, db: AsyncSession = Depends(get_db)):
    """원본 데이터를 삭제합니다. CASCADE로 연결된 분석 결과도 자동 삭제됩니다."""
    stmt = select(RawDataLog).where(RawDataLog.id == data_id)
    record = (await db.execute(stmt)).scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")

    await db.delete(record)
    await db.commit()

    return {"message": f"ID {data_id} 데이터 및 관련 분석 결과가 삭제되었습니다."}


# ---------------------------------------------------------------------------
# POST /api/analyze — Gemini AI 분석 실행
# ---------------------------------------------------------------------------

@router.post("/analyze", response_model=AnalyzeResponse)
async def run_analysis(body: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """Gemini AI를 이용하여 데이터를 분석하고 결과를 저장합니다."""

    # 1. 원본 데이터 조회
    stmt = select(RawDataLog).where(RawDataLog.id == body.raw_data_id)
    raw = (await db.execute(stmt)).scalar_one_or_none()
    if not raw:
        raise HTTPException(status_code=404, detail="원본 데이터를 찾을 수 없습니다.")

    # 2. Gemini API 호출
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.",
        )

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # 데이터 미리보기 (토큰 절약을 위해 최대 50행)
        data_preview = raw.payload[:50] if isinstance(raw.payload, list) else raw.payload

        system_prompt = (
            "너는 데이터 분석 전문가야. 주어진 데이터를 분석해서 반드시 아래 JSON 포맷으로만 답해줘.\n"
            "```json\n"
            '{\n'
            '  "summary": "분석 요약 내용 (한국어, 3~5문장)",\n'
            '  "chart_data": [\n'
            '    {"label": "항목명", "value": 숫자},\n'
            '    ...\n'
            '  ]\n'
            '}\n'
            "```\n"
            "JSON 외에 다른 텍스트는 절대 포함하지 마."
        )

        user_message = f"다음 데이터를 분석해줘.\n\n데이터:\n{json.dumps(data_preview, ensure_ascii=False, default=str)}"
        if body.user_prompt:
            user_message += f"\n\n추가 지시사항: {body.user_prompt}"

        response = model.generate_content([system_prompt, user_message])
        response_text = response.text.strip()

        # JSON 블록 추출
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)
        summary = result.get("summary", "분석 요약을 생성하지 못했습니다.")
        chart_data = result.get("chart_data", [])

    except json.JSONDecodeError:
        logger.warning("Gemini 응답 JSON 파싱 실패, 원본 텍스트를 summary로 저장")
        summary = response_text if 'response_text' in dir() else "분석 결과 파싱 실패"
        chart_data = []
    except Exception as e:
        logger.error(f"Gemini API 호출 실패: {e}")
        raise HTTPException(status_code=500, detail=f"AI 분석 실패: {str(e)}")

    # 3. 결과 저장
    analysis = AnalysisResult(
        raw_data_id=raw.id,
        summary=summary,
        chart_data=chart_data,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    return AnalyzeResponse(
        id=analysis.id,
        raw_data_id=analysis.raw_data_id,
        summary=analysis.summary,
        chart_data=analysis.chart_data if isinstance(analysis.chart_data, list) else [],
    )


# ---------------------------------------------------------------------------
# GET /api/dashboard — 최신 분석 결과 조회
# ---------------------------------------------------------------------------

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
                "raw_data_id": r.raw_data_id,
                "analyzed_at": r.analyzed_at.isoformat(),
                "summary": r.summary,
                "chart_data": r.chart_data,
            }
            for r in rows
        ]
    )

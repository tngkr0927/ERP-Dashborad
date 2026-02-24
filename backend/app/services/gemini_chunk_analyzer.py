"""
Gemini 청크 분할 분석기.

무료 티어 제한을 지키면서 원본 데이터 전체를 Gemini에 전달하기 위해
데이터를 청크로 나눠 각각 분석한 뒤, 마지막에 병합 요청을 보냅니다.

흐름:
  1. DataFrame → JSON 텍스트로 변환
  2. 토큰 제한(약 15만 자 ≈ 안전 마진 포함)에 맞춰 행 단위로 청크 분할
  3. 각 청크를 Gemini에 보내 부분 분석 수행
  4. 모든 부분 분석 결과를 모아 최종 병합 요청
  5. 병합된 summary + chart_data 반환
"""

import asyncio
import json
import logging
import time

import pandas as pd

logger = logging.getLogger(__name__)

# Gemini 2.5 Flash 무료 티어 안전 기준
# 입력 토큰 제한 ~1M이지만, 1글자 ≈ 1~2토큰, 안전하게 15만 자 제한
CHUNK_CHAR_LIMIT = 150_000
# 청크 간 요청 딜레이 (무료 RPM 제한 방지)
REQUEST_DELAY_SEC = 2.0


def _split_dataframe_to_chunks(df: pd.DataFrame, char_limit: int = CHUNK_CHAR_LIMIT) -> list[str]:
    """DataFrame을 JSON 문자열 청크들로 분할합니다.

    각 청크가 char_limit 이하가 되도록 행 단위로 나눕니다.
    """
    records = json.loads(df.to_json(orient="records", force_ascii=False))
    chunks: list[str] = []
    current_batch: list[dict] = []
    current_size = 2  # '[]' 기본 크기

    for record in records:
        record_str = json.dumps(record, ensure_ascii=False)
        record_size = len(record_str) + 2  # comma + space

        if current_size + record_size > char_limit and current_batch:
            chunks.append(json.dumps(current_batch, ensure_ascii=False))
            current_batch = []
            current_size = 2

        current_batch.append(record)
        current_size += record_size

    if current_batch:
        chunks.append(json.dumps(current_batch, ensure_ascii=False))

    return chunks


def _build_chunk_prompt(chunk_json: str, chunk_idx: int, total_chunks: int,
                        columns: list[str], total_rows: int, user_prompt: str) -> tuple[str, str]:
    """청크 분석용 system/user 프롬프트를 생성합니다."""
    system = (
        "너는 데이터 분석 전문가야. "
        f"전체 {total_rows}행 데이터 중 청크 {chunk_idx + 1}/{total_chunks}을 받았어. "
        "이 청크의 데이터를 꼼꼼히 분석하고, 반드시 아래 JSON 포맷으로만 답해줘.\n"
        "```json\n"
        "{\n"
        '  "chunk_summary": "이 청크 데이터의 핵심 분석 (한국어, 3~5문장, 구체적 수치 포함)",\n'
        '  "numeric_aggregates": {"컬럼명": {"합계": 숫자, "건수": 숫자, "최소": 숫자, "최대": 숫자}},\n'
        '  "category_counts": {"컬럼명": {"값": 건수}},\n'
        '  "notable_findings": ["발견1", "발견2"]\n'
        "}\n"
        "```\n"
        "JSON 외에 다른 텍스트는 절대 포함하지 마."
    )

    user = f"컬럼: {columns}\n\n데이터 ({len(json.loads(chunk_json))}행):\n{chunk_json}"
    if user_prompt:
        user += f"\n\n추가 지시사항: {user_prompt}"

    return system, user


def _build_merge_prompt(chunk_results: list[dict], total_rows: int,
                        columns: list[str], user_prompt: str) -> tuple[str, str]:
    """청크 분석 결과들을 병합하는 최종 프롬프트를 생성합니다."""
    system = (
        "너는 데이터 분석 전문가야. "
        f"전체 {total_rows}행 데이터를 청크로 나눠 분석한 결과 {len(chunk_results)}개를 받았어. "
        "이 부분 결과들을 종합하여 전체 데이터에 대한 최종 분석을 만들어줘. "
        "숫자 집계는 모든 청크의 합계/건수를 더해서 정확히 계산해줘. "
        "반드시 아래 JSON 포맷으로만 답해줘.\n"
        "```json\n"
        "{\n"
        '  "summary": "전체 데이터 분석 요약 (한국어, 5~7문장, 구체적 수치 인용)",\n'
        '  "chart_data": [\n'
        '    {"label": "항목명", "value": 숫자},\n'
        "    ...\n"
        "  ]\n"
        "}\n"
        "```\n"
        "chart_data는 가장 의미 있는 항목 5~10개로 구성해줘.\n"
        "JSON 외에 다른 텍스트는 절대 포함하지 마."
    )

    results_json = json.dumps(chunk_results, ensure_ascii=False, default=str)
    user = (
        f"컬럼: {columns}\n"
        f"전체 행수: {total_rows}\n\n"
        f"청크별 분석 결과:\n{results_json}"
    )
    if user_prompt:
        user += f"\n\n추가 지시사항: {user_prompt}"

    return system, user


def _parse_gemini_json(text: str) -> dict:
    """Gemini 응답에서 JSON을 추출하여 파싱합니다."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)


async def analyze_with_chunks(
    df: pd.DataFrame,
    api_key: str,
    user_prompt: str = "",
) -> dict:
    """데이터를 청크로 분할하여 Gemini로 분석하고 병합된 결과를 반환합니다.

    Returns:
        {"summary": str, "chart_data": list[dict]}
    """
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    total_rows = len(df)
    columns = list(df.columns)

    # 1. 청크 분할
    chunks = _split_dataframe_to_chunks(df)
    logger.info(f"데이터 {total_rows}행 → {len(chunks)}개 청크로 분할")

    # 2. 청크가 1개면 바로 최종 분석 (불필요한 2단계 방지)
    if len(chunks) == 1:
        return await _single_pass_analysis(model, df, total_rows, columns, user_prompt)

    # 3. 각 청크별 분석
    chunk_results: list[dict] = []
    for i, chunk_json in enumerate(chunks):
        system, user = _build_chunk_prompt(
            chunk_json, i, len(chunks), columns, total_rows, user_prompt,
        )
        logger.info(f"청크 {i + 1}/{len(chunks)} 분석 요청 ({len(chunk_json):,}자)")

        response = await asyncio.to_thread(
            model.generate_content, [system, user]
        )
        try:
            parsed = _parse_gemini_json(response.text)
            chunk_results.append(parsed)
            logger.info(f"청크 {i + 1}/{len(chunks)} 분석 완료")
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"청크 {i + 1} 파싱 실패: {e}, 원본 텍스트를 저장")
            chunk_results.append({
                "chunk_summary": response.text[:500],
                "notable_findings": ["파싱 실패 — 원본 텍스트 참조"],
            })

        # RPM 제한 방지 딜레이
        if i < len(chunks) - 1:
            await asyncio.sleep(REQUEST_DELAY_SEC)

    # 4. 병합 요청
    logger.info(f"청크 {len(chunk_results)}개 결과 병합 요청")
    system, user = _build_merge_prompt(chunk_results, total_rows, columns, user_prompt)

    response = await asyncio.to_thread(
        model.generate_content, [system, user]
    )
    merged = _parse_gemini_json(response.text)

    return {
        "summary": merged.get("summary", "분석 요약을 생성하지 못했습니다."),
        "chart_data": merged.get("chart_data", []),
    }


async def _single_pass_analysis(model, df: pd.DataFrame, total_rows: int,
                                 columns: list[str], user_prompt: str) -> dict:
    """청크가 1개일 때 단일 요청으로 처리합니다."""
    data_json = json.dumps(
        json.loads(df.to_json(orient="records", force_ascii=False)),
        ensure_ascii=False,
    )

    system = (
        "너는 데이터 분석 전문가야. 아래는 전체 원본 데이터야. "
        "이 데이터를 꼼꼼히 분석하고, 반드시 아래 JSON 포맷으로만 답해줘.\n"
        "```json\n"
        "{\n"
        '  "summary": "전체 데이터 분석 요약 (한국어, 5~7문장, 구체적 수치 인용)",\n'
        '  "chart_data": [\n'
        '    {"label": "항목명", "value": 숫자},\n'
        "    ...\n"
        "  ]\n"
        "}\n"
        "```\n"
        "chart_data는 가장 의미 있는 항목 5~10개로 구성해줘.\n"
        "JSON 외에 다른 텍스트는 절대 포함하지 마."
    )

    user = f"컬럼: {columns}\n전체 {total_rows}행 데이터:\n{data_json}"
    if user_prompt:
        user += f"\n\n추가 지시사항: {user_prompt}"

    response = await asyncio.to_thread(
        model.generate_content, [system, user]
    )
    result = _parse_gemini_json(response.text)

    return {
        "summary": result.get("summary", "분석 요약을 생성하지 못했습니다."),
        "chart_data": result.get("chart_data", []),
    }

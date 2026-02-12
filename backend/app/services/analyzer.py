"""
분석 로직 모듈 (Strategy Pattern).

새로운 분석 로직을 추가하려면:
1. BaseAnalyzer를 상속하는 새 클래스를 만드세요.
2. analyze() 메서드를 구현하세요.
3. ANALYZER_REGISTRY에 등록하세요.
"""

from abc import ABC, abstractmethod

import pandas as pd


class BaseAnalyzer(ABC):
    """
    분석 로직의 추상 베이스 클래스.

    모든 분석기는 이 클래스를 상속하고 analyze() 메서드를 구현해야 합니다.
    """

    @abstractmethod
    def analyze(self, data: pd.DataFrame) -> dict:
        """
        DataFrame을 입력받아 분석 결과를 dict로 반환합니다.

        Args:
            data: 분석할 원본 데이터 (raw_data_logs에서 로드).
        Returns:
            분석 결과 딕셔너리. analysis_results 테이블의 result_data에 저장됩니다.
        """
        ...


class DummyAnalyzer(BaseAnalyzer):
    """
    시스템 동작 확인용 더미 분석기.

    데이터의 행/열 수와 컬럼 목록만 반환합니다.
    """

    def analyze(self, data: pd.DataFrame) -> dict:
        return {
            "row_count": len(data),
            "column_count": len(data.columns),
            "columns": list(data.columns),
            "summary": f"총 {len(data)}건의 데이터가 확인되었습니다.",
        }


# TODO: 새로운 분석기를 구현한 뒤 여기에 등록하세요.
# 예시: "sales_trend": SalesTrendAnalyzer()
ANALYZER_REGISTRY: dict[str, BaseAnalyzer] = {
    "dummy": DummyAnalyzer(),
}


def get_analyzer(analysis_type: str) -> BaseAnalyzer:
    """
    analysis_type 문자열로 등록된 분석기를 조회합니다.

    Raises:
        ValueError: 등록되지 않은 analysis_type인 경우.
    """
    analyzer = ANALYZER_REGISTRY.get(analysis_type)
    if analyzer is None:
        available = ", ".join(ANALYZER_REGISTRY.keys())
        raise ValueError(
            f"Unknown analysis_type: '{analysis_type}'. "
            f"Available: [{available}]"
        )
    return analyzer

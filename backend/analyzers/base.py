"""분석기 기본 인터페이스"""
from abc import ABC, abstractmethod
from models.token import TokenAnalysis


class BaseAnalyzer(ABC):
    """토큰 분석기 추상 클래스"""

    @abstractmethod
    async def analyze(self, address: str) -> TokenAnalysis:
        """
        토큰 분석 실행

        Args:
            address: 토큰 컨트랙트 주소

        Returns:
            TokenAnalysis 결과
        """
        pass

    @abstractmethod
    async def close(self):
        """리소스 정리"""
        pass

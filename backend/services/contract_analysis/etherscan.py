"""Etherscan API 클라이언트 (EVM 체인 공통)"""
import aiohttp
import structlog
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


class EtherscanService:
    """Etherscan/BscScan 등 EVM Explorer API 서비스"""

    def __init__(self, base_url: str, api_key: str = ""):
        self.base_url = base_url
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """HTTP 세션 반환"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session

    async def close(self):
        """세션 종료"""
        if self._session and not self._session.closed:
            await self._session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True
    )
    async def get_contract_source(self, address: str) -> Optional[dict]:
        """
        컨트랙트 소스코드 정보 조회

        Args:
            address: 컨트랙트 주소

        Returns:
            컨트랙트 정보 딕셔너리 또는 None
        """
        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": address,
        }

        if self.api_key:
            params["apikey"] = self.api_key

        logger.debug(
            "etherscan_request",
            endpoint="getsourcecode",
            address=address
        )

        try:
            session = await self._get_session()
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("status") == "1" and data.get("result"):
                        result = data["result"][0] if isinstance(data["result"], list) else data["result"]

                        logger.debug(
                            "etherscan_response",
                            status=200,
                            is_verified=bool(result.get("SourceCode"))
                        )
                        return result
                    else:
                        logger.warning(
                            "etherscan_api_error",
                            status=data.get("status"),
                            message=data.get("message")
                        )
                        return None
                else:
                    logger.warning(
                        "etherscan_http_error",
                        status=response.status,
                        address=address
                    )
                    return None
        except Exception as e:
            logger.error(
                "etherscan_exception",
                error=str(e),
                address=address
            )
            raise

    def parse_contract_data(self, data: dict) -> dict:
        """
        컨트랙트 데이터 파싱

        Args:
            data: Etherscan API 응답

        Returns:
            파싱된 컨트랙트 정보
        """
        if not data:
            return {}

        source_code = data.get("SourceCode", "")
        is_verified = bool(source_code and source_code.strip())

        return {
            "is_verified": is_verified,
            "contract_name": data.get("ContractName") or None,
            "compiler_version": data.get("CompilerVersion") or None,
            "license": data.get("LicenseType") or None,
        }

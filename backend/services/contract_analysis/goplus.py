"""GoPlus Security API 클라이언트"""
import aiohttp
import structlog
from typing import Optional, List
from tenacity import retry, stop_after_attempt, wait_exponential
from models.token import RiskLevel

logger = structlog.get_logger()


class GoPlusService:
    """GoPlus Security API 서비스"""

    BASE_URL = "https://api.gopluslabs.io/api/v1"

    def __init__(self):
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
    async def get_token_security(self, chain_id: str, address: str) -> Optional[dict]:
        """
        토큰 보안 정보 조회

        Args:
            chain_id: GoPlus 체인 ID (1=ETH, 56=BSC, solana 등)
            address: 토큰 컨트랙트 주소

        Returns:
            보안 정보 딕셔너리 또는 None
        """
        url = f"{self.BASE_URL}/token_security/{chain_id}"
        params = {"contract_addresses": address.lower()}

        logger.debug(
            "goplus_request",
            endpoint="token_security",
            chain_id=chain_id,
            address=address
        )

        try:
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("code") == 1:
                        result = data.get("result", {})
                        # 주소를 소문자로 정규화해서 조회
                        token_data = result.get(address.lower(), {})

                        logger.debug(
                            "goplus_response",
                            status=200,
                            has_data=bool(token_data)
                        )
                        return token_data
                    else:
                        logger.warning(
                            "goplus_api_error",
                            code=data.get("code"),
                            message=data.get("message")
                        )
                        return None
                else:
                    logger.warning(
                        "goplus_http_error",
                        status=response.status,
                        chain_id=chain_id,
                        address=address
                    )
                    return None
        except Exception as e:
            logger.error(
                "goplus_exception",
                error=str(e),
                chain_id=chain_id,
                address=address
            )
            raise

    def parse_security_data(self, data: dict) -> dict:
        """
        보안 데이터 파싱 및 위험도 분석

        Args:
            data: GoPlus API 응답

        Returns:
            파싱된 보안 정보
        """
        if not data:
            return {"risk_level": RiskLevel.UNKNOWN, "risk_items": [], "safe_items": []}

        risk_items: List[str] = []
        safe_items: List[str] = []

        # 주요 보안 항목 파싱
        is_open_source = self._parse_bool(data.get("is_open_source"))
        is_proxy = self._parse_bool(data.get("is_proxy"))
        is_mintable = self._parse_bool(data.get("is_mintable"))
        is_honeypot = self._parse_bool(data.get("is_honeypot"))
        can_take_back_ownership = self._parse_bool(data.get("can_take_back_ownership"))
        hidden_owner = self._parse_bool(data.get("hidden_owner"))
        selfdestruct = self._parse_bool(data.get("selfdestruct"))
        external_call = self._parse_bool(data.get("external_call"))
        slippage_modifiable = self._parse_bool(data.get("slippage_modifiable"))
        is_blacklisted = self._parse_bool(data.get("is_blacklisted"))
        is_whitelisted = self._parse_bool(data.get("is_whitelisted"))
        is_anti_whale = self._parse_bool(data.get("is_anti_whale"))
        trading_cooldown = self._parse_bool(data.get("trading_cooldown"))
        transfer_pausable = self._parse_bool(data.get("transfer_pausable"))

        # 세금 파싱
        buy_tax = self._parse_float(data.get("buy_tax"))
        sell_tax = self._parse_float(data.get("sell_tax"))

        # 위험 항목 분석
        # Critical risks
        if is_honeypot:
            risk_items.append("HONEYPOT detected - Cannot sell!")
        if selfdestruct:
            risk_items.append("Self-destruct function found")
        if hidden_owner:
            risk_items.append("Hidden owner detected")

        # High risks
        if can_take_back_ownership:
            risk_items.append("Owner can reclaim ownership")
        if is_mintable:
            risk_items.append("Owner can mint new tokens")
        if slippage_modifiable:
            risk_items.append("Slippage can be modified")
        if transfer_pausable:
            risk_items.append("Transfers can be paused")

        # Medium risks
        if is_proxy:
            risk_items.append("Proxy contract (upgradeable)")
        if external_call:
            risk_items.append("External calls detected")
        if is_blacklisted:
            risk_items.append("Blacklist function exists")
        if is_whitelisted:
            risk_items.append("Whitelist function exists")
        if trading_cooldown:
            risk_items.append("Trading cooldown enabled")
        if is_anti_whale:
            risk_items.append("Anti-whale mechanism")

        # Tax warnings
        if buy_tax is not None and buy_tax > 5:
            risk_items.append(f"High buy tax: {buy_tax}%")
        if sell_tax is not None and sell_tax > 5:
            risk_items.append(f"High sell tax: {sell_tax}%")

        # Safe items
        if is_open_source:
            safe_items.append("Open source (verified)")
        elif is_open_source is False:
            risk_items.append("Source code not verified")

        if is_honeypot is False:
            safe_items.append("Not a honeypot")
        if is_mintable is False:
            safe_items.append("Not mintable")
        if can_take_back_ownership is False:
            safe_items.append("Ownership cannot be reclaimed")
        if buy_tax is not None and buy_tax == 0:
            safe_items.append("No buy tax")
        if sell_tax is not None and sell_tax == 0:
            safe_items.append("No sell tax")

        # 위험도 계산
        risk_level = self._calculate_risk_level(risk_items, is_honeypot, selfdestruct)

        return {
            "is_open_source": is_open_source,
            "is_proxy": is_proxy,
            "is_mintable": is_mintable,
            "is_honeypot": is_honeypot,
            "can_take_back_ownership": can_take_back_ownership,
            "hidden_owner": hidden_owner,
            "selfdestruct": selfdestruct,
            "external_call": external_call,
            "buy_tax": buy_tax,
            "sell_tax": sell_tax,
            "slippage_modifiable": slippage_modifiable,
            "is_blacklisted": is_blacklisted,
            "is_whitelisted": is_whitelisted,
            "is_anti_whale": is_anti_whale,
            "trading_cooldown": trading_cooldown,
            "transfer_pausable": transfer_pausable,
            "holder_count": self._parse_int(data.get("holder_count")),
            "owner": data.get("owner_address"),
            "risk_level": risk_level,
            "risk_items": risk_items,
            "safe_items": safe_items,
        }

    def _calculate_risk_level(
        self,
        risk_items: List[str],
        is_honeypot: Optional[bool],
        selfdestruct: Optional[bool]
    ) -> RiskLevel:
        """위험도 레벨 계산"""
        if is_honeypot or selfdestruct:
            return RiskLevel.CRITICAL

        risk_count = len(risk_items)

        if risk_count == 0:
            return RiskLevel.LOW
        elif risk_count <= 2:
            return RiskLevel.MEDIUM
        elif risk_count <= 4:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    @staticmethod
    def _parse_bool(value) -> Optional[bool]:
        """문자열/숫자를 bool로 변환"""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value == "1"
        if isinstance(value, (int, float)):
            return value == 1
        return None

    @staticmethod
    def _parse_float(value) -> Optional[float]:
        """안전한 float 변환 (퍼센트)"""
        if value is None:
            return None
        try:
            return float(value) * 100  # 비율을 퍼센트로 변환
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_int(value) -> Optional[int]:
        """안전한 int 변환"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

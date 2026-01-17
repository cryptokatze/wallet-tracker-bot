"""EVM 체인 분석기"""
import asyncio
import structlog
from web3 import Web3
from typing import Optional

from analyzers.base import BaseAnalyzer
from config.chains import ChainConfig
from models.token import (
    TokenAnalysis,
    TokenBasicInfo,
    TokenSecurityInfo,
    TokenMarketInfo,
    ContractInfo,
    RiskLevel
)
from services.contract_analysis.dexscreener import DEXScreenerService
from services.contract_analysis.goplus import GoPlusService
from services.contract_analysis.etherscan import EtherscanService

logger = structlog.get_logger()

# ERC20 기본 ABI
ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]


class EVMAnalyzer(BaseAnalyzer):
    """EVM 체인 (ETH, BSC, Arbitrum, Base) 분석기"""

    def __init__(self, chain: str, config: ChainConfig):
        self.chain = chain
        self.config = config
        self.web3 = Web3(Web3.HTTPProvider(config.rpc_url))

        # 서비스 초기화
        self.dexscreener = DEXScreenerService()
        self.goplus = GoPlusService()
        self.etherscan = EtherscanService(
            base_url=config.explorer_api,
            api_key=config.explorer_api_key
        ) if config.explorer_api else None

    async def analyze(self, address: str) -> TokenAnalysis:
        """
        토큰 분석 실행

        Args:
            address: 토큰 컨트랙트 주소

        Returns:
            TokenAnalysis 결과
        """
        logger.info(
            "evm_analysis_started",
            chain=self.chain,
            address=address
        )

        analysis = TokenAnalysis(
            chain=self.chain,
            chain_name=self.config.name,
            address=address
        )

        # 병렬로 모든 데이터 수집
        tasks = [
            self._get_basic_info(address),
            self._get_security_info(address),
            self._get_market_info(address),
        ]

        if self.etherscan:
            tasks.append(self._get_contract_info(address))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 처리
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = f"Error in task {i}: {str(result)}"
                logger.error("analysis_task_error", task_index=i, error=str(result))
                analysis.errors.append(error_msg)
            elif result is not None:
                if i == 0:  # basic info
                    analysis.basic = TokenBasicInfo(**result)
                elif i == 1:  # security info
                    analysis.security = TokenSecurityInfo(**result)
                    # GoPlus에서 홀더 수와 오너 정보 병합
                    if result.get("holder_count"):
                        analysis.basic.holder_count = result["holder_count"]
                    if result.get("owner"):
                        analysis.basic.owner = result["owner"]
                elif i == 2:  # market info
                    analysis.market = TokenMarketInfo(**result)
                elif i == 3:  # contract info
                    analysis.contract = ContractInfo(**result)

        logger.info(
            "evm_analysis_completed",
            chain=self.chain,
            address=address,
            risk_level=analysis.security.risk_level.value,
            errors_count=len(analysis.errors)
        )

        return analysis

    async def _get_basic_info(self, address: str) -> Optional[dict]:
        """Web3로 기본 정보 조회"""
        try:
            checksum_address = Web3.to_checksum_address(address)
            contract = self.web3.eth.contract(address=checksum_address, abi=ERC20_ABI)

            # 동기 호출을 비동기로 래핑
            loop = asyncio.get_event_loop()

            name = await loop.run_in_executor(None, contract.functions.name().call)
            symbol = await loop.run_in_executor(None, contract.functions.symbol().call)
            decimals = await loop.run_in_executor(None, contract.functions.decimals().call)
            total_supply_raw = await loop.run_in_executor(None, contract.functions.totalSupply().call)

            total_supply = total_supply_raw / (10 ** decimals)

            # 큰 숫자 포맷팅
            if total_supply >= 1_000_000_000_000:
                formatted = f"{total_supply / 1_000_000_000_000:.2f}T"
            elif total_supply >= 1_000_000_000:
                formatted = f"{total_supply / 1_000_000_000:.2f}B"
            elif total_supply >= 1_000_000:
                formatted = f"{total_supply / 1_000_000:.2f}M"
            elif total_supply >= 1_000:
                formatted = f"{total_supply / 1_000:.2f}K"
            else:
                formatted = f"{total_supply:.2f}"

            logger.debug(
                "basic_info_fetched",
                name=name,
                symbol=symbol,
                decimals=decimals
            )

            return {
                "name": name,
                "symbol": symbol,
                "decimals": decimals,
                "total_supply": total_supply,
                "total_supply_formatted": formatted,
            }

        except Exception as e:
            logger.error("basic_info_error", error=str(e), address=address)
            return None

    async def _get_security_info(self, address: str) -> Optional[dict]:
        """GoPlus로 보안 정보 조회"""
        try:
            data = await self.goplus.get_token_security(
                self.config.goplus_chain_id,
                address
            )

            if data:
                return self.goplus.parse_security_data(data)
            return {"risk_level": RiskLevel.UNKNOWN, "risk_items": [], "safe_items": []}

        except Exception as e:
            logger.error("security_info_error", error=str(e), address=address)
            return None

    async def _get_market_info(self, address: str) -> Optional[dict]:
        """DEXScreener로 시장 정보 조회"""
        try:
            pairs = await self.dexscreener.get_token_pairs(
                self.config.dexscreener_id,
                address
            )

            if pairs:
                return self.dexscreener.parse_market_data(pairs)
            return {}

        except Exception as e:
            logger.error("market_info_error", error=str(e), address=address)
            return None

    async def _get_contract_info(self, address: str) -> Optional[dict]:
        """Etherscan으로 컨트랙트 정보 조회"""
        try:
            data = await self.etherscan.get_contract_source(address)

            if data:
                return self.etherscan.parse_contract_data(data)
            return {}

        except Exception as e:
            logger.error("contract_info_error", error=str(e), address=address)
            return None

    async def close(self):
        """리소스 정리"""
        await self.dexscreener.close()
        await self.goplus.close()
        if self.etherscan:
            await self.etherscan.close()

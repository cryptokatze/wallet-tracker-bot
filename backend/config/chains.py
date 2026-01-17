"""체인별 설정 (Contract Analysis용)"""
from dataclasses import dataclass
from typing import Optional
from functools import lru_cache


@dataclass
class ChainConfig:
    """체인 설정"""
    name: str
    chain_id: Optional[int]
    goplus_chain_id: str
    rpc_url: str
    explorer_api: Optional[str]
    explorer_api_key: str
    dexscreener_id: str
    symbol: str
    is_evm: bool = True


@lru_cache()
def get_chain_configs() -> dict[str, ChainConfig]:
    """체인 설정 딕셔너리 반환"""
    from config.base import settings

    return {
        "ethereum": ChainConfig(
            name="Ethereum",
            chain_id=1,
            goplus_chain_id="1",
            rpc_url=settings.eth_rpc_url,
            explorer_api="https://api.etherscan.io/api",
            explorer_api_key=settings.etherscan_api_key,
            dexscreener_id="ethereum",
            symbol="ETH"
        ),
        "bsc": ChainConfig(
            name="BNB Chain",
            chain_id=56,
            goplus_chain_id="56",
            rpc_url=settings.bsc_rpc_url,
            explorer_api="https://api.bscscan.com/api",
            explorer_api_key=settings.bscscan_api_key,
            dexscreener_id="bsc",
            symbol="BNB"
        ),
        "arbitrum": ChainConfig(
            name="Arbitrum",
            chain_id=42161,
            goplus_chain_id="42161",
            rpc_url=settings.arb_rpc_url,
            explorer_api="https://api.arbiscan.io/api",
            explorer_api_key=settings.arbiscan_api_key,
            dexscreener_id="arbitrum",
            symbol="ETH"
        ),
        "base": ChainConfig(
            name="Base",
            chain_id=8453,
            goplus_chain_id="8453",
            rpc_url=settings.base_rpc_url,
            explorer_api="https://api.basescan.org/api",
            explorer_api_key=settings.basescan_api_key,
            dexscreener_id="base",
            symbol="ETH"
        ),
        "solana": ChainConfig(
            name="Solana",
            chain_id=None,
            goplus_chain_id="solana",
            rpc_url=settings.solana_rpc_url,
            explorer_api=None,
            explorer_api_key="",
            dexscreener_id="solana",
            symbol="SOL",
            is_evm=False
        )
    }


# 지원하는 EVM 체인 목록
EVM_CHAINS = ["ethereum", "bsc", "arbitrum", "base"]

# 모든 지원 체인
ALL_CHAINS = EVM_CHAINS + ["solana"]

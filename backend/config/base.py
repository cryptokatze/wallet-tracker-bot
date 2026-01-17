"""설정 관리"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from loguru import logger


class Settings(BaseSettings):
    """앱 설정"""

    # Telegram
    telegram_bot_token: str = ""

    # Moralis (EVM)
    moralis_api_key: str = ""

    # Helius (Solana)
    helius_api_key: str = ""
    helius_webhook_secret: str = ""  # 웹훅 인증용 시크릿

    # Webhook Server
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8000

    # Dashboard
    dashboard_enabled: bool = False
    dashboard_path: str = "../frontend/dist"

    # Database
    database_path: str = "./data/wallets.db"

    # Logging
    log_level: str = "INFO"

    # RPC URLs (Contract Analysis)
    eth_rpc_url: str = "https://eth.llamarpc.com"
    bsc_rpc_url: str = "https://bsc-dataseed.binance.org"
    arb_rpc_url: str = "https://arb1.arbitrum.io/rpc"
    base_rpc_url: str = "https://mainnet.base.org"
    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"

    # Explorer API Keys (Contract Analysis)
    etherscan_api_key: str = ""
    bscscan_api_key: str = ""
    arbiscan_api_key: str = ""
    basescan_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 설정 인스턴스
settings = Settings()


def validate_required_settings() -> list[str]:
    """
    필수 환경변수 검증

    Returns:
        누락된 설정 목록 (빈 리스트면 모두 설정됨)
    """
    warnings = []

    # 웹훅 사용시 필수
    if not settings.moralis_api_key:
        warnings.append("MORALIS_API_KEY: EVM 웹훅 인증에 필요")

    if not settings.helius_webhook_secret:
        warnings.append("HELIUS_WEBHOOK_SECRET: Solana 웹훅 인증에 필요")

    return warnings


# 로거 설정
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True,
)

# DB 디렉토리 생성
Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)

# 지원 체인 목록
SUPPORTED_CHAINS = {
    # EVM 체인 (Moralis)
    "eth": {"name": "Ethereum", "chain_id": "0x1", "explorer": "etherscan.io"},
    "bsc": {"name": "BSC", "chain_id": "0x38", "explorer": "bscscan.com"},
    "polygon": {"name": "Polygon", "chain_id": "0x89", "explorer": "polygonscan.com"},
    "arb": {"name": "Arbitrum", "chain_id": "0xa4b1", "explorer": "arbiscan.io"},
    "base": {"name": "Base", "chain_id": "0x2105", "explorer": "basescan.org"},
    "op": {"name": "Optimism", "chain_id": "0xa", "explorer": "optimistic.etherscan.io"},
    "avax": {"name": "Avalanche", "chain_id": "0xa86a", "explorer": "snowtrace.io"},
    # Solana (Helius)
    "sol": {"name": "Solana", "chain_id": "solana", "explorer": "solscan.io"},
}

# DEX 컨트랙트 주소 (스왑 감지용)
DEX_CONTRACTS = {
    "eth": {
        "uniswap_v2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "sushiswap": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
    },
    "bsc": {
        "pancakeswap_v2": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
        "pancakeswap_v3": "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4",
    },
    "arb": {
        "uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "sushiswap": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
    },
    "base": {
        "uniswap_v3": "0x2626664c2603336E57B271c5C0b26F421741e481",
    },
    "sol": {
        "jupiter": "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
        "raydium": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
    },
}

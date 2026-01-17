"""토큰 분석 데이터 모델"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """위험도 레벨"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class TokenBasicInfo(BaseModel):
    """토큰 기본 정보"""
    name: str = Field(default="Unknown")
    symbol: str = Field(default="???")
    decimals: int = Field(default=18)
    total_supply: Optional[float] = None
    total_supply_formatted: Optional[str] = None
    holder_count: Optional[int] = None
    owner: Optional[str] = None


class TokenSecurityInfo(BaseModel):
    """토큰 보안 정보"""
    is_open_source: Optional[bool] = None
    is_proxy: Optional[bool] = None
    is_mintable: Optional[bool] = None
    is_honeypot: Optional[bool] = None
    can_take_back_ownership: Optional[bool] = None
    hidden_owner: Optional[bool] = None
    selfdestruct: Optional[bool] = None
    external_call: Optional[bool] = None
    buy_tax: Optional[float] = None
    sell_tax: Optional[float] = None
    slippage_modifiable: Optional[bool] = None
    is_blacklisted: Optional[bool] = None
    is_whitelisted: Optional[bool] = None
    is_anti_whale: Optional[bool] = None
    trading_cooldown: Optional[bool] = None
    transfer_pausable: Optional[bool] = None
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    risk_items: List[str] = Field(default_factory=list)
    safe_items: List[str] = Field(default_factory=list)


class TokenMarketInfo(BaseModel):
    """토큰 시장 정보"""
    price_usd: Optional[float] = None
    price_native: Optional[float] = None
    price_change_5m: Optional[float] = None
    price_change_1h: Optional[float] = None
    price_change_6h: Optional[float] = None
    price_change_24h: Optional[float] = None
    liquidity_usd: Optional[float] = None
    liquidity_base: Optional[float] = None
    liquidity_quote: Optional[float] = None
    base_token_symbol: Optional[str] = None
    quote_token_symbol: Optional[str] = None
    fdv: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    volume_1h: Optional[float] = None
    volume_6h: Optional[float] = None
    txns_24h_buys: Optional[int] = None
    txns_24h_sells: Optional[int] = None
    dex_name: Optional[str] = None
    pair_address: Optional[str] = None
    pair_url: Optional[str] = None
    pair_created_at: Optional[int] = None


class ContractInfo(BaseModel):
    """컨트랙트 정보"""
    is_verified: Optional[bool] = None
    compiler_version: Optional[str] = None
    license: Optional[str] = None
    contract_name: Optional[str] = None


class TokenAnalysis(BaseModel):
    """토큰 분석 결과"""
    chain: str
    chain_name: str
    address: str
    basic: TokenBasicInfo = Field(default_factory=TokenBasicInfo)
    security: TokenSecurityInfo = Field(default_factory=TokenSecurityInfo)
    market: TokenMarketInfo = Field(default_factory=TokenMarketInfo)
    contract: ContractInfo = Field(default_factory=ContractInfo)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    errors: List[str] = Field(default_factory=list)

    def has_errors(self) -> bool:
        """에러 발생 여부"""
        return len(self.errors) > 0

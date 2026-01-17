"""텔레그램 메시지 포맷팅"""
from models.token import TokenAnalysis, RiskLevel
from config.chains import get_chain_configs


def format_analysis_result(analysis: TokenAnalysis) -> str:
    """
    분석 결과를 텔레그램 메시지로 포맷팅

    Args:
        analysis: TokenAnalysis 결과

    Returns:
        HTML 포맷된 메시지
    """
    lines = []

    # 헤더
    lines.append("<b>Token Analysis Report</b>")
    lines.append("")

    # 기본 정보
    lines.append("<b>Basic Info</b>")
    lines.append(f"Name: <code>{escape_html(analysis.basic.name)}</code>")
    lines.append(f"Symbol: <code>{escape_html(analysis.basic.symbol)}</code>")
    lines.append(f"Chain: {analysis.chain_name}")

    if analysis.basic.total_supply_formatted:
        lines.append(f"Total Supply: {analysis.basic.total_supply_formatted}")

    if analysis.basic.holder_count:
        lines.append(f"Holders: {format_number(analysis.basic.holder_count)}")

    lines.append("")

    # 시장 정보
    if analysis.market.price_usd is not None:
        lines.append("<b>Market Data</b>")

        price_str = format_price(analysis.market.price_usd)
        change_str = ""
        if analysis.market.price_change_24h is not None:
            change = analysis.market.price_change_24h
            emoji = "+" if change >= 0 else ""
            change_str = f" ({emoji}{change:.1f}% 24h)"
        lines.append(f"Price: ${price_str}{change_str}")

        if analysis.market.market_cap:
            lines.append(f"MCap: ${format_number(analysis.market.market_cap)}")

        if analysis.market.fdv:
            lines.append(f"FDV: ${format_number(analysis.market.fdv)}")

        lines.append("")

        # LP 유동성 정보
        lines.append("<b>LP Liquidity</b>")
        if analysis.market.liquidity_usd:
            lines.append(f"Total: ${format_number(analysis.market.liquidity_usd)}")

        if analysis.market.liquidity_base and analysis.market.base_token_symbol:
            lines.append(f"{analysis.market.base_token_symbol}: {format_number(analysis.market.liquidity_base)}")

        if analysis.market.liquidity_quote and analysis.market.quote_token_symbol:
            lines.append(f"{analysis.market.quote_token_symbol}: {format_number(analysis.market.liquidity_quote)}")

        if analysis.market.dex_name:
            lines.append(f"DEX: {analysis.market.dex_name}")

        if analysis.market.pair_address:
            short_pair = f"{analysis.market.pair_address[:6]}...{analysis.market.pair_address[-4:]}"
            lines.append(f"Pair: <code>{short_pair}</code>")

        lines.append("")

        # 거래량
        lines.append("<b>Volume</b>")
        if analysis.market.volume_1h:
            lines.append(f"1h: ${format_number(analysis.market.volume_1h)}")
        if analysis.market.volume_6h:
            lines.append(f"6h: ${format_number(analysis.market.volume_6h)}")
        if analysis.market.volume_24h:
            lines.append(f"24h: ${format_number(analysis.market.volume_24h)}")

        if analysis.market.txns_24h_buys or analysis.market.txns_24h_sells:
            buys = analysis.market.txns_24h_buys or 0
            sells = analysis.market.txns_24h_sells or 0
            lines.append(f"Txns 24h: {buys} buys / {sells} sells")

        lines.append("")

    # 보안 정보
    lines.append("<b>Security Analysis</b>")
    lines.append(f"Risk Level: {format_risk_badge(analysis.security.risk_level)}")
    lines.append("")

    # 안전 항목
    if analysis.security.safe_items:
        for item in analysis.security.safe_items[:5]:
            lines.append(f"  {item}")

    # 위험 항목
    if analysis.security.risk_items:
        lines.append("")
        lines.append("<b>Warnings:</b>")
        for item in analysis.security.risk_items[:8]:
            lines.append(f"  {item}")

    lines.append("")

    # 컨트랙트 검증 정보
    if analysis.contract.is_verified is not None:
        status = "Verified" if analysis.contract.is_verified else "Not Verified"
        lines.append(f"Contract: {status}")

    # 링크
    lines.append("")
    lines.append("<b>Links</b>")
    links = get_explorer_links(analysis.chain, analysis.address)
    lines.append(links)

    # 에러 표시
    if analysis.errors:
        lines.append("")
        lines.append("<b>Errors:</b>")
        for error in analysis.errors[:3]:
            lines.append(f"  {escape_html(error[:50])}")

    # 타임스탬프
    lines.append("")
    lines.append(f"<i>Analyzed: {analysis.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')} UTC</i>")

    return "\n".join(lines)


def format_risk_badge(level: RiskLevel) -> str:
    """위험도 배지 생성"""
    badges = {
        RiskLevel.LOW: "LOW RISK",
        RiskLevel.MEDIUM: "MEDIUM RISK",
        RiskLevel.HIGH: "HIGH RISK",
        RiskLevel.CRITICAL: "CRITICAL RISK",
        RiskLevel.UNKNOWN: "UNKNOWN",
    }
    return badges.get(level, "UNKNOWN")


def format_price(price: float) -> str:
    """가격 포맷팅"""
    if price >= 1:
        return f"{price:,.2f}"
    elif price >= 0.0001:
        return f"{price:.6f}"
    else:
        return f"{price:.10f}"


def format_number(num: float) -> str:
    """큰 숫자 포맷팅"""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.2f}K"
    else:
        return f"{num:,.0f}"


def get_explorer_links(chain: str, address: str) -> str:
    """체인별 익스플로러 링크 생성"""
    explorers = {
        "ethereum": f"https://etherscan.io/token/{address}",
        "bsc": f"https://bscscan.com/token/{address}",
        "arbitrum": f"https://arbiscan.io/token/{address}",
        "base": f"https://basescan.org/token/{address}",
        "solana": f"https://solscan.io/token/{address}",
    }

    chain_configs = get_chain_configs()
    dex_id = chain_configs.get(chain, {})
    if hasattr(dex_id, 'dexscreener_id'):
        dex_id = dex_id.dexscreener_id
    else:
        dex_id = chain

    explorer = explorers.get(chain, "")
    dexscreener = f"https://dexscreener.com/{dex_id}/{address}"
    goplus = f"https://gopluslabs.io/token-security/{chain}/{address}"

    links = []
    if explorer:
        links.append(f'<a href="{explorer}">Explorer</a>')
    links.append(f'<a href="{dexscreener}">DEXScreener</a>')
    links.append(f'<a href="{goplus}">GoPlus</a>')

    return " | ".join(links)


def escape_html(text: str) -> str:
    """HTML 이스케이프"""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def format_loading_message(chain: str, address: str) -> str:
    """로딩 메시지 포맷팅"""
    short_addr = f"{address[:6]}...{address[-4:]}"
    return f"Analyzing <code>{short_addr}</code> on {chain}..."

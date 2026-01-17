"""Moralis 웹훅 처리 - 실시간 가격 연동

EVM 체인 트랜잭션 처리 (ETH, BSC, Polygon, Arbitrum, Base, Optimism, Avalanche)
"""
from loguru import logger

from config import SUPPORTED_CHAINS, DEX_CONTRACTS
from services.price_service import PriceService
from .processor import TransactionProcessor, TransferInfo


# 체인별 네이티브 토큰 심볼
NATIVE_SYMBOLS = {
    "eth": "ETH",
    "bsc": "BNB",
    "polygon": "MATIC",
    "arb": "ETH",
    "base": "ETH",
    "op": "ETH",
    "avax": "AVAX",
}


async def process_moralis_webhook(data: dict):
    """Moralis 웹훅 데이터 처리"""
    if not data.get("confirmed"):
        logger.debug("Skipping unconfirmed transaction")
        return

    txs = data.get("txs", [])
    erc20_transfers = data.get("erc20Transfers", [])
    chain_id = data.get("chainId")

    # 체인 코드 찾기
    chain_code = None
    for code, info in SUPPORTED_CHAINS.items():
        if info.get("chain_id") == chain_id:
            chain_code = code
            break

    if not chain_code:
        logger.warning(f"Unknown chain ID: {chain_id}")
        return

    logger.info(f"Processing {len(txs)} txs, {len(erc20_transfers)} token transfers on {chain_code}")

    # 네이티브 트랜잭션 처리
    for tx in txs:
        await process_native_tx(tx, chain_code)

    # ERC20 전송 처리
    for transfer in erc20_transfers:
        await process_erc20_transfer(transfer, chain_code)


async def process_native_tx(tx: dict, chain: str):
    """네이티브 트랜잭션 처리"""
    from_addr = tx.get("fromAddress", "").lower()
    to_addr = tx.get("toAddress", "").lower()
    value_wei = int(tx.get("value", 0))
    tx_hash = tx.get("hash", "")

    # 값이 없으면 스킵 (컨트랙트 호출일 수 있음)
    if value_wei == 0:
        await check_dex_swap(tx, chain)
        return

    # ETH 단위로 변환
    value_eth = value_wei / 1e18
    symbol = NATIVE_SYMBOLS.get(chain, "???")

    # 실시간 USD 가격 조회
    value_usd = await PriceService.get_usd_value(chain, value_eth)

    logger.debug(
        f"Native tx: {from_addr[:10]}... -> {to_addr[:10]}... "
        f"| {value_eth:.4f} {symbol} (${value_usd:.2f})"
    )

    # 공통 프로세서로 알림 처리
    await TransactionProcessor.process_transfer(
        TransferInfo(
            from_addr=from_addr,
            to_addr=to_addr,
            chain=chain,
            tx_type="Transfer",
            amount=f"{value_eth:.4f} {symbol}",
            amount_usd=value_usd,
            tx_hash=tx_hash,
        )
    )


async def process_erc20_transfer(transfer: dict, chain: str):
    """ERC20 전송 처리"""
    from_addr = transfer.get("from", "").lower()
    to_addr = transfer.get("to", "").lower()
    value = int(transfer.get("value", 0))
    decimals = int(transfer.get("tokenDecimals", 18))
    symbol = transfer.get("tokenSymbol", "???")
    contract_address = transfer.get("contract", "").lower()
    tx_hash = transfer.get("transactionHash", "")

    amount = value / (10 ** decimals)

    # 실시간 토큰 USD 가격 조회
    value_usd = await PriceService.get_usd_value(chain, amount, contract_address)

    logger.debug(
        f"ERC20 tx: {from_addr[:10]}... -> {to_addr[:10]}... "
        f"| {amount:.4f} {symbol} (${value_usd:.2f})"
    )

    # 공통 프로세서로 알림 처리
    await TransactionProcessor.process_transfer(
        TransferInfo(
            from_addr=from_addr,
            to_addr=to_addr,
            chain=chain,
            tx_type="Token Transfer",
            amount=f"{amount:.4f} {symbol}",
            amount_usd=value_usd,
            tx_hash=tx_hash,
        )
    )


async def check_dex_swap(tx: dict, chain: str):
    """DEX 스왑 감지"""
    to_addr = tx.get("toAddress", "").lower()
    from_addr = tx.get("fromAddress", "").lower()
    tx_hash = tx.get("hash", "")
    logs = tx.get("logs", [])

    dex_contracts = DEX_CONTRACTS.get(chain, {})
    dex_name = None

    for name, addr in dex_contracts.items():
        if to_addr == addr.lower():
            dex_name = name.replace("_", " ").title()
            break

    if not dex_name:
        return

    # 스왑 상세 파싱 시도
    swap_details = await parse_swap_logs(logs, chain)
    swap_summary = swap_details.get("summary", "Unknown swap")
    value_usd = swap_details.get("usd_value", 0)

    logger.info(f"DEX Swap detected: {dex_name} | {swap_summary}")

    # 공통 프로세서로 알림 처리
    await TransactionProcessor.process_swap(
        from_addr=from_addr,
        chain=chain,
        swap_summary=swap_summary,
        amount_usd=value_usd,
        tx_hash=tx_hash,
        dex_name=dex_name,
    )


async def parse_swap_logs(logs: list, chain: str) -> dict:
    """스왑 로그 파싱하여 상세 정보 추출"""
    # Uniswap V2 Swap 이벤트 시그니처
    SWAP_V2_TOPIC = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
    # Uniswap V3 Swap 이벤트 시그니처
    SWAP_V3_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"

    result = {
        "token_in": None,
        "token_out": None,
        "amount_in": 0,
        "amount_out": 0,
        "summary": "",
        "usd_value": 0,
    }

    for log in logs:
        topic0 = log.get("topic0", "")

        if topic0 == SWAP_V2_TOPIC:
            # Uniswap V2 Swap 이벤트 파싱
            try:
                data = log.get("data", "")
                if data and len(data) >= 258:
                    # data format: amount0In, amount1In, amount0Out, amount1Out
                    amount0_in = int(data[2:66], 16)
                    amount1_in = int(data[66:130], 16)
                    amount0_out = int(data[130:194], 16)
                    amount1_out = int(data[194:258], 16)

                    # 0 값 체크 후 안전하게 처리
                    if amount0_in > 0 and amount1_out > 0:
                        result["amount_in"] = amount0_in / 1e18
                        result["amount_out"] = amount1_out / 1e18
                    elif amount1_in > 0 and amount0_out > 0:
                        result["amount_in"] = amount1_in / 1e18
                        result["amount_out"] = amount0_out / 1e18
                    else:
                        logger.debug("V2 swap: both amounts are 0, skipping")
                        continue

                    result["summary"] = f"{result['amount_in']:.4f} -> {result['amount_out']:.4f}"
            except Exception as e:
                logger.debug(f"Failed to parse V2 swap log: {e}")

        elif topic0 == SWAP_V3_TOPIC:
            # Uniswap V3 Swap 이벤트 파싱
            try:
                data = log.get("data", "")
                if data and len(data) >= 194:
                    # amount0, amount1 (signed int256)
                    amount0 = int(data[2:66], 16)
                    amount1 = int(data[66:130], 16)

                    # signed 변환 (uint256 -> int256)
                    if amount0 >= 2**255:
                        amount0 -= 2**256
                    if amount1 >= 2**255:
                        amount1 -= 2**256

                    # 둘 다 0이면 스킵
                    if amount0 == 0 and amount1 == 0:
                        logger.debug("V3 swap: both amounts are 0, skipping")
                        continue

                    if amount0 < 0:
                        result["amount_out"] = abs(amount0) / 1e18
                        result["amount_in"] = max(amount1, 0) / 1e18
                    else:
                        result["amount_in"] = amount0 / 1e18
                        result["amount_out"] = abs(amount1) / 1e18

                    result["summary"] = f"{result['amount_in']:.4f} -> {result['amount_out']:.4f}"
            except Exception as e:
                logger.debug(f"Failed to parse V3 swap log: {e}")

    return result

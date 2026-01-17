"""Helius 웹훅 처리 (Solana) - 실시간 가격 연동

Solana 체인 트랜잭션 처리 (SOL, SPL 토큰)
"""
from loguru import logger

from services.price_service import PriceService
from .processor import TransactionProcessor, TransferInfo


async def process_helius_webhook(data: list):
    """Helius 웹훅 데이터 처리"""
    if not isinstance(data, list):
        data = [data]

    logger.info(f"Processing {len(data)} Solana transactions")

    for tx in data:
        await process_solana_tx(tx)


async def process_solana_tx(tx: dict):
    """Solana 트랜잭션 처리"""
    tx_type = tx.get("type", "UNKNOWN")
    signature = tx.get("signature", "")

    logger.debug(f"Solana tx: type={tx_type}, sig={signature[:20]}...")

    # 스왑 감지
    if tx_type == "SWAP":
        await process_swap(tx, signature)
        return

    # 토큰 전송
    token_transfers = tx.get("tokenTransfers", [])
    native_transfers = tx.get("nativeTransfers", [])

    # 네이티브 SOL 전송
    for transfer in native_transfers:
        await process_native_transfer(transfer, signature)

    # SPL 토큰 전송
    for transfer in token_transfers:
        await process_token_transfer(transfer, signature)


async def process_native_transfer(transfer: dict, signature: str):
    """네이티브 SOL 전송 처리"""
    from_addr = transfer.get("fromUserAccount", "").lower()
    to_addr = transfer.get("toUserAccount", "").lower()
    amount_lamports = transfer.get("amount", 0)
    amount_sol = amount_lamports / 1e9

    # 실시간 SOL USD 가격 조회
    value_usd = await PriceService.get_usd_value("sol", amount_sol)

    logger.debug(
        f"SOL transfer: {from_addr[:10]}... -> {to_addr[:10]}... "
        f"| {amount_sol:.4f} SOL (${value_usd:.2f})"
    )

    # 공통 프로세서로 알림 처리
    await TransactionProcessor.process_transfer(
        TransferInfo(
            from_addr=from_addr,
            to_addr=to_addr,
            chain="sol",
            tx_type="Transfer",
            amount=f"{amount_sol:.4f} SOL",
            amount_usd=value_usd,
            tx_hash=signature,
        )
    )


async def process_token_transfer(transfer: dict, signature: str):
    """SPL 토큰 전송 처리"""
    from_addr = transfer.get("fromUserAccount", "").lower()
    to_addr = transfer.get("toUserAccount", "").lower()
    amount = transfer.get("tokenAmount", 0)
    symbol = transfer.get("tokenSymbol", "???")
    mint = transfer.get("mint", "")

    # 실시간 SPL 토큰 USD 가격 조회
    value_usd = await PriceService.get_usd_value("sol", amount, mint)

    logger.debug(
        f"SPL transfer: {from_addr[:10]}... -> {to_addr[:10]}... "
        f"| {amount:.4f} {symbol} (${value_usd:.2f})"
    )

    # 공통 프로세서로 알림 처리
    await TransactionProcessor.process_transfer(
        TransferInfo(
            from_addr=from_addr,
            to_addr=to_addr,
            chain="sol",
            tx_type="Token Transfer",
            amount=f"{amount:.4f} {symbol}",
            amount_usd=value_usd,
            tx_hash=signature,
        )
    )


async def process_swap(tx: dict, signature: str):
    """스왑 트랜잭션 처리"""
    fee_payer = tx.get("feePayer", "").lower()
    description = tx.get("description", "")

    # 스왑 상세 파싱
    swap_info = tx.get("events", {}).get("swap", {})

    native_input = swap_info.get("nativeInput", {})
    native_output = swap_info.get("nativeOutput", {})
    token_inputs = swap_info.get("tokenInputs", [])
    token_outputs = swap_info.get("tokenOutputs", [])

    # 매도/매수 정보 구성
    sell_info = ""
    buy_info = ""
    value_usd = 0

    if native_input:
        amount_sol = native_input.get("amount", 0) / 1e9
        sell_info = f"{amount_sol:.4f} SOL"
        value_usd = await PriceService.get_usd_value("sol", amount_sol)
    elif token_inputs:
        ti = token_inputs[0]
        amount = ti.get("tokenAmount", 0)
        symbol = ti.get("tokenSymbol", "???")
        mint = ti.get("mint", "")
        sell_info = f"{amount:.4f} {symbol}"
        value_usd = await PriceService.get_usd_value("sol", amount, mint)

    if native_output:
        amount_sol = native_output.get("amount", 0) / 1e9
        buy_info = f"{amount_sol:.4f} SOL"
    elif token_outputs:
        to = token_outputs[0]
        buy_info = f"{to.get('tokenAmount', 0):.4f} {to.get('tokenSymbol', '???')}"

    swap_summary = f"{sell_info} -> {buy_info}" if sell_info and buy_info else description

    logger.info(f"Solana Swap: {swap_summary} (${value_usd:.2f})")

    # 공통 프로세서로 알림 처리
    await TransactionProcessor.process_swap(
        from_addr=fee_payer,
        chain="sol",
        swap_summary=swap_summary,
        amount_usd=value_usd,
        tx_hash=signature,
        dex_name="Jupiter/Raydium",
    )

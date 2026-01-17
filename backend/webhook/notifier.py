"""텔레그램 알림 전송"""
from telegram import Bot
from loguru import logger

from config import settings, SUPPORTED_CHAINS

# 봇 인스턴스 (lazy init)
_bot: Bot | None = None


def get_bot() -> Bot:
    """봇 인스턴스 반환"""
    global _bot
    if _bot is None:
        _bot = Bot(token=settings.telegram_bot_token)
    return _bot


async def send_notification(
    user_id: int,
    label: str,
    chain: str,
    tx_type: str,
    direction: str,
    amount: str,
    amount_usd: float,
    counterparty: str,
    tx_hash: str,
    is_swap: bool = False,
):
    """텔레그램 알림 전송"""
    chain_info = SUPPORTED_CHAINS.get(chain, {})
    chain_name = chain_info.get("name", chain.upper())
    explorer = chain_info.get("explorer", "")

    # 탐색기 URL 생성
    if chain == "sol":
        tx_url = f"https://{explorer}/tx/{tx_hash}"
    else:
        tx_url = f"https://{explorer}/tx/{tx_hash}"

    # 메시지 구성
    if is_swap:
        emoji = "\U0001F504"  # 🔄
        message = f"""
{emoji} <b>[{label}] DEX 스왑 감지!</b>

체인: {chain_name}
DEX: {counterparty}
스왑: {amount}

<a href="{tx_url}">트랜잭션 보기</a>
"""
    else:
        emoji = "\U0001F514" if direction == "OUT" else "\U0001F4E5"  # 🔔 or 📥
        direction_text = "OUT" if direction == "OUT" else "IN"
        usd_text = f" (${amount_usd:,.0f})" if amount_usd > 0 else ""

        short_addr = f"{counterparty[:10]}...{counterparty[-6:]}" if len(counterparty) > 20 else counterparty

        message = f"""
{emoji} <b>[{label}] 트랜잭션 감지!</b>

체인: {chain_name}
유형: {tx_type}
방향: {direction_text}
금액: {amount}{usd_text}
{"To" if direction == "OUT" else "From"}: <code>{short_addr}</code>

<a href="{tx_url}">트랜잭션 보기</a>
"""

    try:
        bot = get_bot()
        await bot.send_message(
            chat_id=user_id,
            text=message.strip(),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        logger.info(f"Notification sent to {user_id}: {label} {tx_type}")
    except Exception as e:
        logger.error(
            f"Failed to send notification to user {user_id} ({label}): {e}",
            exc_info=True
        )

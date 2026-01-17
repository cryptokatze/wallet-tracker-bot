"""텔레그램 봇 핸들러 - 주소 검증 강화"""
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from loguru import logger

from db.crud import WalletCRUD
from config.base import SUPPORTED_CHAINS
from services.moralis_api import MoralisAPI
from services.helius_api import HeliusAPI
from utils.validators import validate_address


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """시작 명령어"""
    welcome_text = """
<b>Crypto Tracker Bot</b>

지갑 추적 + 컨트랙트 분석 올인원 봇

<b>지갑 추적:</b>
/add &lt;체인&gt; &lt;주소&gt; &lt;라벨&gt; - 지갑 추가
/list - 추적 중인 지갑 목록
/remove &lt;라벨&gt; - 지갑 삭제
/toggle &lt;라벨&gt; - incoming 알림 on/off
/filter &lt;라벨&gt; &lt;금액&gt; - 최소 금액 필터 ($)
/chains - 지원 체인 목록

<b>컨트랙트 분석:</b>
주소만 보내면 자동 분석!
- EVM: <code>0x...</code> (체인 선택)
- Solana: base58 주소

<b>예시:</b>
<code>/add eth 0x123...abc whale1</code>
<code>0xdAC17F958D2ee523a2206206994597C13D831ec7</code>
    """
    await update.message.reply_text(welcome_text, parse_mode="HTML")


async def chains(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """지원 체인 목록"""
    text = "<b>지원 체인</b>\n\n"
    for code, info in SUPPORTED_CHAINS.items():
        text += f"<code>{code}</code> - {info['name']}\n"
    await update.message.reply_text(text, parse_mode="HTML")


async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """지갑 추가 - 검증 강화, 스트림 생성 우선"""
    user_id = update.effective_user.id
    args = context.args

    if len(args) < 3:
        await update.message.reply_text(
            "사용법: <code>/add &lt;체인&gt; &lt;주소&gt; &lt;라벨&gt;</code>\n"
            "예시: <code>/add eth 0x123...abc whale1</code>",
            parse_mode="HTML",
        )
        return

    chain = args[0].lower()
    address = args[1]
    label = args[2]

    # 체인 검증
    if chain not in SUPPORTED_CHAINS:
        await update.message.reply_text(
            f"지원하지 않는 체인: {chain}\n/chains 명령어로 지원 체인을 확인하세요."
        )
        return

    # 주소 검증 (강화)
    is_valid, result = validate_address(chain, address)
    if not is_valid:
        await update.message.reply_text(
            f"유효하지 않은 주소입니다.\n"
            f"오류: {result}",
            parse_mode="HTML",
        )
        logger.warning(f"Invalid address from user {user_id}: {address[:20]}... ({result})")
        return

    # 정규화된 주소 사용
    normalized_address = result

    # 라벨 중복 확인
    existing = await WalletCRUD.get_wallet_by_label(user_id, label)
    if existing:
        await update.message.reply_text(f"이미 '{label}' 라벨이 존재합니다.")
        return

    # 주소 중복 확인 (같은 사용자)
    existing_addr = await WalletCRUD.get_wallet_by_address_for_user(user_id, normalized_address)
    if existing_addr:
        await update.message.reply_text(
            f"이미 추적 중인 주소입니다.\n"
            f"라벨: {existing_addr['label']}"
        )
        return

    try:
        # 1. 스트림/웹훅 먼저 생성 (실패시 DB 저장 안함)
        await update.message.reply_text("스트림 생성 중...")

        stream_id = None
        if chain == "sol":
            stream_id = await HeliusAPI.create_webhook(normalized_address, label)
        else:
            stream_id = await MoralisAPI.create_stream(chain, normalized_address, label)

        if not stream_id:
            await update.message.reply_text(
                "스트림 생성 실패!\n"
                "API 키를 확인하거나 나중에 다시 시도하세요.\n\n"
                "환경변수 확인:\n"
                f"- {'HELIUS_API_KEY' if chain == 'sol' else 'MORALIS_API_KEY'}"
            )
            logger.error(f"Failed to create stream for {label} on {chain}")
            return

        # 2. 성공시에만 DB에 저장
        wallet_id = await WalletCRUD.add_wallet(
            user_id, chain, normalized_address, label, stream_id
        )

        chain_name = SUPPORTED_CHAINS[chain]["name"]
        await update.message.reply_text(
            f"<b>지갑 추가 완료!</b>\n\n"
            f"라벨: <code>{label}</code>\n"
            f"체인: {chain_name}\n"
            f"주소: <code>{normalized_address[:10]}...{normalized_address[-8:]}</code>\n"
            f"스트림 ID: <code>{stream_id[:16]}...</code>",
            parse_mode="HTML",
        )
        logger.info(f"User {user_id} added wallet: {label} ({chain})")

    except Exception as e:
        logger.error(f"Failed to add wallet: {e}", exc_info=True)
        await update.message.reply_text(f"지갑 추가 실패: {e}")


async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """지갑 목록"""
    user_id = update.effective_user.id
    wallets = await WalletCRUD.get_wallets(user_id)

    if not wallets:
        await update.message.reply_text("추적 중인 지갑이 없습니다.\n/add 명령어로 지갑을 추가하세요.")
        return

    text = "<b>추적 중인 지갑</b>\n\n"
    for w in wallets:
        chain_name = SUPPORTED_CHAINS.get(w["chain"], {}).get("name", w["chain"])
        incoming = "ON" if w["incoming_enabled"] else "OFF"
        min_amt = f"${w['min_amount_usd']:.0f}" if w["min_amount_usd"] > 0 else "-"
        stream_status = "OK" if w.get("stream_id") else "NO STREAM"

        text += (
            f"<b>{w['label']}</b>\n"
            f"  체인: {chain_name}\n"
            f"  주소: <code>{w['address'][:10]}...{w['address'][-6:]}</code>\n"
            f"  Incoming: {incoming} | 최소금액: {min_amt}\n"
            f"  상태: {stream_status}\n\n"
        )

    await update.message.reply_text(text, parse_mode="HTML")


async def remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """지갑 삭제"""
    user_id = update.effective_user.id
    args = context.args

    if not args:
        await update.message.reply_text("사용법: <code>/remove &lt;라벨&gt;</code>", parse_mode="HTML")
        return

    label = args[0]

    # 지갑 조회
    wallet = await WalletCRUD.get_wallet_by_label(user_id, label)
    if not wallet:
        await update.message.reply_text(f"'{label}' 지갑을 찾을 수 없습니다.")
        return

    # 스트림/웹훅 삭제
    if wallet.get("stream_id"):
        try:
            if wallet["chain"] == "sol":
                await HeliusAPI.delete_webhook(wallet["stream_id"])
            else:
                await MoralisAPI.delete_stream(wallet["stream_id"])
            logger.info(f"Stream deleted: {wallet['stream_id'][:16]}...")
        except Exception as e:
            logger.warning(f"Failed to delete stream: {e}")

    # DB에서 삭제
    if await WalletCRUD.remove_wallet(user_id, label):
        await update.message.reply_text(f"'{label}' 지갑을 삭제했습니다.")
        logger.info(f"User {user_id} removed wallet: {label}")
    else:
        await update.message.reply_text(f"'{label}' 지갑 삭제 실패.")


async def toggle_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """incoming 토글"""
    user_id = update.effective_user.id
    args = context.args

    if not args:
        await update.message.reply_text("사용법: <code>/toggle &lt;라벨&gt;</code>", parse_mode="HTML")
        return

    label = args[0]
    result = await WalletCRUD.toggle_incoming(user_id, label)

    if result is None:
        await update.message.reply_text(f"'{label}' 지갑을 찾을 수 없습니다.")
    else:
        status = "ON" if result else "OFF"
        await update.message.reply_text(f"'{label}' Incoming 알림: <b>{status}</b>", parse_mode="HTML")
        logger.info(f"User {user_id} toggled incoming for {label}: {status}")


async def set_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """금액 필터 설정"""
    user_id = update.effective_user.id
    args = context.args

    if len(args) < 2:
        await update.message.reply_text(
            "사용법: <code>/filter &lt;라벨&gt; &lt;금액&gt;</code>\n"
            "예시: <code>/filter whale1 1000</code> (= $1000 이상만 알림)",
            parse_mode="HTML",
        )
        return

    label = args[0]
    try:
        amount = float(args[1])
        if amount < 0:
            await update.message.reply_text("금액은 0 이상이어야 합니다.")
            return
    except ValueError:
        await update.message.reply_text("금액은 숫자로 입력하세요.")
        return

    if await WalletCRUD.set_min_amount(user_id, label, amount):
        await update.message.reply_text(
            f"'{label}' 최소 금액 필터: <b>${amount:.0f}</b>", parse_mode="HTML"
        )
        logger.info(f"User {user_id} set filter for {label}: ${amount}")
    else:
        await update.message.reply_text(f"'{label}' 지갑을 찾을 수 없습니다.")


def setup_handlers(app: Application):
    """핸들러 등록"""
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("chains", chains))
    app.add_handler(CommandHandler("add", add_wallet))
    app.add_handler(CommandHandler("list", list_wallets))
    app.add_handler(CommandHandler("remove", remove_wallet))
    app.add_handler(CommandHandler("toggle", toggle_incoming))
    app.add_handler(CommandHandler("filter", set_filter))

    logger.info("Telegram handlers registered")

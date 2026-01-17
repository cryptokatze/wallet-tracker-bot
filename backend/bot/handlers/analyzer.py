"""컨트랙트 분석 핸들러"""
from loguru import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.chains import get_chain_configs, EVM_CHAINS
from analyzers.evm_analyzer import EVMAnalyzer
from analyzers.solana_analyzer import SolanaAnalyzer
from utils.validators import extract_address
from utils.formatters import format_analysis_result, format_loading_message


async def handle_analyze_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    일반 메시지 처리 - 주소 감지 및 분석
    명령어가 아닌 메시지에서 주소를 감지하면 분석 시작
    """
    text = update.message.text.strip()
    user = update.effective_user

    logger.info(f"Message received from user {user.id}: {len(text)} chars")

    # 주소 추출
    address, addr_type = extract_address(text)

    if not address:
        # 주소가 없으면 무시 (wallet 명령어 등 다른 용도일 수 있음)
        return False  # 처리 안됨 표시

    logger.info(f"Address detected: {address[:10]}... ({addr_type})")

    if addr_type == "solana":
        # 솔라나는 바로 분석
        await analyze_solana(update, context, address)

    elif addr_type == "evm":
        # EVM은 체인 선택 필요
        await show_chain_selection(update, context, address)

    return True  # 처리됨 표시


async def show_chain_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, address: str):
    """
    EVM 체인 선택 키보드 표시
    """
    chains = get_chain_configs()

    keyboard = []
    row = []

    for i, chain_id in enumerate(EVM_CHAINS):
        chain = chains[chain_id]
        callback_data = f"analyze:{chain_id}:{address}"

        row.append(InlineKeyboardButton(chain.name, callback_data=callback_data))

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    short_addr = f"{address[:6]}...{address[-4:]}"
    await update.message.reply_text(
        f"Address: <code>{short_addr}</code>\n\nSelect the chain to analyze:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def handle_analyze_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    인라인 버튼 콜백 처리 (체인 선택)
    """
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("analyze:"):
        parts = data.split(":", 2)
        if len(parts) == 3:
            _, chain, address = parts
            await analyze_evm(query, context, chain, address)
            return True

    return False


async def analyze_evm(query, context: ContextTypes.DEFAULT_TYPE, chain: str, address: str):
    """
    EVM 토큰 분석 실행
    """
    user = query.from_user
    logger.info(f"EVM analysis requested by {user.id}: {chain} / {address[:10]}...")

    chains = get_chain_configs()
    config = chains.get(chain)

    if not config:
        await query.edit_message_text("Invalid chain selected.")
        return

    # 로딩 메시지
    loading_msg = format_loading_message(config.name, address)
    await query.edit_message_text(loading_msg, parse_mode="HTML")

    # 분석 실행
    analyzer = EVMAnalyzer(chain, config)

    try:
        result = await analyzer.analyze(address)

        # 결과 포맷팅 및 전송
        message = format_analysis_result(result)
        await query.edit_message_text(
            message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        logger.info(
            f"EVM analysis completed: {chain}/{address[:10]}... "
            f"risk={result.security.risk_level.value}"
        )

    except Exception as e:
        logger.error(f"EVM analysis failed: {chain}/{address[:10]}... error={e}")

        await query.edit_message_text(
            f"Analysis failed: {str(e)[:100]}\n\nPlease try again later."
        )

    finally:
        await analyzer.close()


async def analyze_solana(update: Update, context: ContextTypes.DEFAULT_TYPE, address: str):
    """
    솔라나 토큰 분석 실행
    """
    user = update.effective_user
    logger.info(f"Solana analysis requested by {user.id}: {address[:10]}...")

    chains = get_chain_configs()
    config = chains.get("solana")

    # 로딩 메시지
    loading_msg = format_loading_message("Solana", address)
    status_message = await update.message.reply_text(loading_msg, parse_mode="HTML")

    # 분석 실행
    analyzer = SolanaAnalyzer(config)

    try:
        result = await analyzer.analyze(address)

        # DEXScreener에서 이름/심볼 업데이트
        if hasattr(result.market, '_name') and result.market._name:
            result.basic.name = result.market._name
        if hasattr(result.market, '_symbol') and result.market._symbol:
            result.basic.symbol = result.market._symbol

        # 결과 포맷팅 및 전송
        message = format_analysis_result(result)
        await status_message.edit_text(
            message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        logger.info(
            f"Solana analysis completed: {address[:10]}... "
            f"risk={result.security.risk_level.value}"
        )

    except Exception as e:
        logger.error(f"Solana analysis failed: {address[:10]}... error={e}")

        await status_message.edit_text(
            f"Analysis failed: {str(e)[:100]}\n\nPlease try again later."
        )

    finally:
        await analyzer.close()

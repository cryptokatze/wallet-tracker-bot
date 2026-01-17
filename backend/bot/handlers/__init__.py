"""Bot handlers 모듈"""
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from loguru import logger

from bot.handlers.wallet import (
    start,
    chains,
    add_wallet,
    list_wallets,
    remove_wallet,
    toggle_incoming,
    set_filter,
)
from bot.handlers.analyzer import (
    handle_analyze_message,
    handle_analyze_callback,
)


def setup_handlers(app: Application):
    """모든 핸들러 등록"""
    # 명령어 핸들러 (Wallet Tracking)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("chains", chains))
    app.add_handler(CommandHandler("add", add_wallet))
    app.add_handler(CommandHandler("list", list_wallets))
    app.add_handler(CommandHandler("remove", remove_wallet))
    app.add_handler(CommandHandler("toggle", toggle_incoming))
    app.add_handler(CommandHandler("filter", set_filter))

    # 콜백 쿼리 핸들러 (Contract Analysis - 체인 선택)
    app.add_handler(CallbackQueryHandler(handle_analyze_callback))

    # 일반 메시지 핸들러 (Contract Analysis - 주소 감지)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_analyze_message)
    )

    logger.info("All handlers registered (wallet + analyzer)")

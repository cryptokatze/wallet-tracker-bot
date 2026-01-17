"""
Crypto Tracker Bot - 메인 진입점

멀티체인 지갑 추적 + 컨트랙트 분석 통합 봇
- Graceful shutdown 지원
- 시그널 핸들링 (SIGTERM, SIGINT)
"""
import asyncio
import signal
import sys
import threading
import uvicorn
from telegram.ext import Application
from loguru import logger

from config.base import settings, validate_required_settings
from db.models import init_db, close_db
from bot.handlers import setup_handlers
from webhook.server import create_app
from services.http_client import close_http_client

# 종료 이벤트
shutdown_event = asyncio.Event()


async def run_telegram_bot():
    """텔레그램 봇 실행"""
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set! Running webhook server only...")
        # 종료 신호 대기 (웹훅 서버만 실행)
        try:
            await shutdown_event.wait()
        except asyncio.CancelledError:
            pass
        return

    app = Application.builder().token(settings.telegram_bot_token).build()
    setup_handlers(app)

    logger.info("Starting Telegram bot...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    # 종료 신호 대기
    try:
        await shutdown_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Stopping Telegram bot...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        logger.info("Telegram bot stopped")


def run_webhook_server(stop_event: threading.Event):
    """웹훅 서버 실행 (별도 스레드)"""
    app = create_app()

    class CustomServer(uvicorn.Server):
        def install_signal_handlers(self):
            # 시그널 핸들러 비활성화 (메인 스레드에서 처리)
            pass

    config = uvicorn.Config(
        app,
        host=settings.webhook_host,
        port=settings.webhook_port,
        log_level="warning",  # uvicorn 로그 줄임
        lifespan="off",  # lifespan 비활성화로 종료 에러 방지
    )
    server = CustomServer(config)

    # 별도 스레드에서 실행
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def serve_with_stop():
        """서버 실행 + 종료 체크"""
        server_task = asyncio.create_task(server.serve())

        while not stop_event.is_set() and not server_task.done():
            await asyncio.sleep(0.3)

        # 서버 종료
        server.should_exit = True
        try:
            await asyncio.wait_for(server_task, timeout=3.0)
        except asyncio.TimeoutError:
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass

    try:
        loop.run_until_complete(serve_with_stop())
    except Exception as e:
        logger.debug(f"Webhook server stopped: {e}")
    finally:
        # 남은 태스크 정리
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()


def signal_handler(sig, frame):
    """시그널 핸들러"""
    logger.info(f"Received signal {sig}, initiating shutdown...")
    shutdown_event.set()


async def main():
    """메인 함수"""
    logger.info("=" * 50)
    logger.info("Crypto Tracker Bot Starting...")
    logger.info("(Wallet Tracking + Contract Analysis)")
    logger.info("=" * 50)

    # 환경변수 검증
    missing_settings = validate_required_settings()
    if missing_settings:
        logger.warning("=" * 50)
        logger.warning("SECURITY WARNING: Missing required settings")
        for warning in missing_settings:
            logger.warning(f"  - {warning}")
        logger.warning("Webhooks may not work correctly!")
        logger.warning("=" * 50)

    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # DB 초기화
    await init_db()

    # 웹훅 서버 종료 이벤트
    webhook_stop_event = threading.Event()

    # 웹훅 서버 (별도 스레드)
    webhook_thread = threading.Thread(
        target=run_webhook_server,
        args=(webhook_stop_event,),
        daemon=False,  # 정상 종료 대기
    )
    webhook_thread.start()
    logger.info(f"Webhook server started on port {settings.webhook_port}")

    # 텔레그램 봇 실행
    try:
        await run_telegram_bot()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
        shutdown_event.set()
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down...")

        # 웹훅 서버 종료
        webhook_stop_event.set()
        webhook_thread.join(timeout=5)
        logger.info("Webhook server stopped")

        # HTTP 클라이언트 종료
        await close_http_client()

        # DB 종료
        await close_db()

        logger.info("=" * 50)
        logger.info("Crypto Tracker Bot Stopped. Goodbye!")
        logger.info("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    sys.exit(0)

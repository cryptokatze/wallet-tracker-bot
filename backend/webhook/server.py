"""FastAPI 웹훅 서버 - 인증 강화 + Rate Limiting + 대시보드 서빙"""
import time
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config.base import settings
from utils.signature import verify_moralis_signature, verify_helius_auth
from .moralis import process_moralis_webhook
from .helius import process_helius_webhook

# Rate Limiter 설정 (IP 기반)
limiter = Limiter(key_func=get_remote_address)


def create_app() -> FastAPI:
    """FastAPI 앱 생성"""
    app = FastAPI(title="Crypto Tracker API")

    # Rate Limiter 등록
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.get("/health")
    async def health():
        """헬스 체크"""
        return {"status": "ok", "timestamp": int(time.time())}

    @app.post("/webhook/moralis")
    @limiter.limit("60/minute")  # IP당 분당 60회 제한
    async def moralis_webhook(request: Request):
        """
        Moralis 웹훅 엔드포인트

        Moralis는 X-Signature 헤더로 서명 전송
        """
        start_time = time.time()

        # 원본 body (서명 검증용)
        body = await request.body()

        # 서명 검증 (API 키 없으면 거부)
        signature = request.headers.get("x-signature", "")
        if not settings.moralis_api_key:
            logger.error("SECURITY: MORALIS_API_KEY not configured - rejecting webhook")
            raise HTTPException(status_code=503, detail="Webhook not configured")

        if not verify_moralis_signature(body, signature, settings.moralis_api_key):
            logger.warning(
                f"Moralis webhook signature verification failed. "
                f"IP: {request.client.host if request.client else 'unknown'}"
            )
            raise HTTPException(status_code=401, detail="Invalid signature")

        try:
            # JSON 파싱
            import json
            data = json.loads(body)

            tx_count = len(data.get("txs", []))
            chain_id = data.get("chainId", "unknown")
            logger.info(
                f"Moralis webhook received: chain={chain_id}, txs={tx_count}"
            )
            # 보안: 페이로드 전체 로깅 제거 (민감정보 포함 가능)

            await process_moralis_webhook(data)

            elapsed = time.time() - start_time
            logger.info(f"Moralis webhook processed in {elapsed:.3f}s")

            return {"status": "ok", "processed": tx_count}

        except json.JSONDecodeError as e:
            logger.error(f"Moralis webhook JSON parse error: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        except Exception as e:
            logger.error(f"Moralis webhook error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.post("/webhook/helius")
    @limiter.limit("60/minute")  # IP당 분당 60회 제한
    async def helius_webhook(
        request: Request,
        auth: Optional[str] = Query(None, description="인증 토큰")
    ):
        """
        Helius 웹훅 엔드포인트

        Helius는 URL 쿼리로 auth 토큰 전송
        예: /webhook/helius?auth=your_secret_token
        """
        start_time = time.time()

        # 인증 검증
        if not verify_helius_auth(auth or "", settings.helius_webhook_secret):
            logger.warning(
                f"Helius webhook auth failed. "
                f"IP: {request.client.host if request.client else 'unknown'}"
            )
            raise HTTPException(status_code=401, detail="Unauthorized")

        try:
            body = await request.json()

            # body는 리스트 형태
            tx_count = len(body) if isinstance(body, list) else 1
            logger.info(f"Helius webhook received: txs={tx_count}")
            # 보안: 페이로드 전체 로깅 제거 (민감정보 포함 가능)

            await process_helius_webhook(body)

            elapsed = time.time() - start_time
            logger.info(f"Helius webhook processed in {elapsed:.3f}s")

            return {"status": "ok", "processed": tx_count}

        except Exception as e:
            logger.error(f"Helius webhook error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    # 대시보드 서빙 (DASHBOARD_ENABLED=true 일 때)
    if settings.dashboard_enabled:
        dashboard_dir = Path(settings.dashboard_path).resolve()

        if dashboard_dir.exists():
            logger.info(f"Dashboard enabled: serving from {dashboard_dir}")

            # SPA 라우팅을 위한 catch-all
            @app.get("/{full_path:path}")
            async def serve_spa(full_path: str):
                """SPA 라우팅 - 모든 경로에서 index.html 반환"""
                # API 경로는 제외 (슬래시 없이 시작점 체크)
                if full_path.startswith(("webhook", "health", "api")):
                    raise HTTPException(status_code=404)

                # 정적 파일 있으면 서빙 (Path Traversal 방어)
                file_path = (dashboard_dir / full_path).resolve()
                if not file_path.is_relative_to(dashboard_dir):
                    logger.warning(f"Path traversal attempt: {full_path}")
                    raise HTTPException(status_code=403, detail="Forbidden")
                if file_path.exists() and file_path.is_file():
                    return FileResponse(file_path)

                # 없으면 index.html (SPA 라우팅)
                return FileResponse(dashboard_dir / "index.html")

            # 정적 파일 (assets 등)
            assets_dir = dashboard_dir / "assets"
            if assets_dir.exists():
                app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        else:
            logger.warning(f"Dashboard path not found: {dashboard_dir}")
            logger.warning("Run 'npm run build' in frontend/ to build dashboard")

    return app

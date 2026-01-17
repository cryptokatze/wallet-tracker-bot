"""웹훅 서명 검증 유틸리티"""
import hashlib
import hmac
from loguru import logger


def verify_moralis_signature(
    body: bytes,
    signature: str,
    api_key: str
) -> bool:
    """
    Moralis 웹훅 서명 검증

    Moralis는 Web3 SHA3 (Keccak-256)를 사용:
    signature = keccak256(body + api_key)

    Args:
        body: 원본 요청 본문 (bytes)
        signature: X-Signature 헤더 값
        api_key: Moralis API 키

    Returns:
        bool: 서명 유효 여부
    """
    if not signature or not api_key:
        logger.warning("Missing signature or API key for verification")
        return False

    try:
        # Keccak-256 (SHA3) 사용
        from eth_hash.auto import keccak

        # body + api_key 를 바이트로 변환하여 해시
        data = body + api_key.encode("utf-8")
        calculated = keccak(data).hex()

        # 0x 접두사 처리
        if signature.startswith("0x"):
            signature = signature[2:]
        if calculated.startswith("0x"):
            calculated = calculated[2:]

        is_valid = hmac.compare_digest(calculated.lower(), signature.lower())

        if is_valid:
            logger.debug("Moralis signature verified successfully")
        else:
            # 보안: 예상 서명을 로그에 노출하지 않음
            logger.warning("Moralis signature mismatch")

        return is_valid

    except ImportError:
        # eth_hash 없으면 검증 불가 - 보안상 거부
        logger.error(
            "SECURITY: eth_hash not installed - cannot verify Moralis signatures! "
            "Install with: pip install eth-hash[pycryptodome]"
        )
        return False

    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


def verify_helius_auth(auth_token: str, expected_token: str) -> bool:
    """
    Helius 웹훅 인증 토큰 검증

    Args:
        auth_token: URL 쿼리에서 받은 auth 토큰
        expected_token: 설정된 시크릿 토큰

    Returns:
        bool: 인증 성공 여부
    """
    if not expected_token:
        # 시크릿 미설정시 보안상 거부
        logger.warning(
            "SECURITY: HELIUS_WEBHOOK_SECRET not configured! "
            "All Helius webhooks will be rejected."
        )
        return False

    if not auth_token:
        logger.warning("Missing auth token in Helius webhook request")
        return False

    is_valid = hmac.compare_digest(auth_token, expected_token)

    if is_valid:
        logger.debug("Helius auth verified successfully")
    else:
        logger.warning("Helius auth token mismatch")

    return is_valid

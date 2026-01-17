"""주소 유효성 검증 유틸리티"""
import re
from typing import Tuple, Optional
from loguru import logger


def validate_evm_address(address: str) -> Tuple[bool, str]:
    """
    EVM 주소 유효성 검증

    Returns:
        Tuple[bool, str]: (유효 여부, 에러 메시지 또는 정규화된 주소)
    """
    if not address:
        return False, "주소가 비어있습니다"

    # 0x 접두사 확인
    if not address.startswith("0x"):
        return False, "EVM 주소는 0x로 시작해야 합니다"

    # 길이 확인 (0x + 40자)
    if len(address) != 42:
        return False, f"주소 길이가 42자여야 합니다 (현재: {len(address)}자)"

    # 16진수 형식 확인
    if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
        return False, "유효하지 않은 16진수 형식입니다"

    # Checksum 검증 (선택적 - web3 없이도 동작)
    try:
        from eth_utils import to_checksum_address, is_checksum_address

        checksummed = to_checksum_address(address)
        logger.debug(f"EVM address validated: {checksummed[:10]}...")
        return True, checksummed
    except ImportError:
        # eth_utils 없으면 기본 검증만
        logger.debug(f"EVM address validated (no checksum): {address[:10]}...")
        return True, address.lower()
    except Exception as e:
        logger.warning(f"Checksum validation failed: {e}")
        return True, address.lower()


def validate_solana_address(address: str) -> Tuple[bool, str]:
    """
    Solana 주소 유효성 검증 (Base58)

    Returns:
        Tuple[bool, str]: (유효 여부, 에러 메시지 또는 원본 주소)
    """
    if not address:
        return False, "주소가 비어있습니다"

    # 길이 확인 (32-44자)
    if len(address) < 32 or len(address) > 44:
        return False, f"Solana 주소는 32-44자여야 합니다 (현재: {len(address)}자)"

    # Base58 문자 확인 (0, O, I, l 제외)
    base58_pattern = r"^[1-9A-HJ-NP-Za-km-z]+$"
    if not re.match(base58_pattern, address):
        return False, "유효하지 않은 Base58 형식입니다"

    # Base58 디코딩 검증
    try:
        import base58

        decoded = base58.b58decode(address)
        if len(decoded) != 32:
            return False, f"디코딩된 주소가 32바이트여야 합니다 (현재: {len(decoded)}바이트)"

        logger.debug(f"Solana address validated: {address[:10]}...")
        return True, address
    except ImportError:
        # base58 없으면 기본 검증만
        logger.debug(f"Solana address validated (no decode): {address[:10]}...")
        return True, address
    except Exception as e:
        return False, f"Base58 디코딩 실패: {e}"


def validate_address(chain: str, address: str) -> Tuple[bool, str]:
    """
    체인에 따른 주소 검증

    Args:
        chain: 체인 코드 (eth, sol, bsc 등)
        address: 검증할 주소

    Returns:
        Tuple[bool, str]: (유효 여부, 에러 메시지 또는 정규화된 주소)
    """
    if chain == "sol":
        return validate_solana_address(address)
    else:
        return validate_evm_address(address)


def detect_address_type(address: str) -> str:
    """
    주소 형식 감지

    Args:
        address: 입력된 주소

    Returns:
        "evm", "solana", 또는 "unknown"
    """
    address = address.strip()

    # EVM 주소: 0x로 시작, 40자의 hex
    if re.match(r'^0x[a-fA-F0-9]{40}$', address):
        return "evm"

    # Solana 주소: base58, 32-44자
    if re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address):
        return "solana"

    return "unknown"


def extract_address(text: str) -> Tuple[Optional[str], str]:
    """
    텍스트에서 주소 추출

    Args:
        text: 사용자 입력 텍스트

    Returns:
        (주소, 타입) 튜플. 주소가 없으면 (None, "unknown")
    """
    text = text.strip()

    # EVM 주소 추출
    evm_match = re.search(r'0x[a-fA-F0-9]{40}', text)
    if evm_match:
        return evm_match.group(), "evm"

    # Solana 주소 추출 (단어 경계로 구분)
    base58_pattern = r'^[1-9A-HJ-NP-Za-km-z]{32,44}$'
    words = text.split()
    for word in words:
        if re.match(base58_pattern, word):
            return word, "solana"

    return None, "unknown"

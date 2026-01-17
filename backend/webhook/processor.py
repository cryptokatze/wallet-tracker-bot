"""트랜잭션 처리 공통 로직

지갑 필터링 + 알림 발송 패턴을 추상화하여 코드 중복 제거
"""
from dataclasses import dataclass
from typing import Optional
from loguru import logger

from db.crud import WalletCRUD
from .notifier import send_notification


@dataclass
class TransferInfo:
    """전송 정보 데이터 클래스"""
    from_addr: str
    to_addr: str
    chain: str
    tx_type: str  # "Transfer", "Token Transfer", "DEX Swap"
    amount: str  # "0.5 ETH", "100 USDC"
    amount_usd: float
    tx_hash: str
    is_swap: bool = False
    counterparty_name: Optional[str] = None  # DEX 이름 등


class TransactionProcessor:
    """트랜잭션 처리 공통 클래스

    지갑 필터링, min_amount 체크, 알림 발송 로직을 통합
    """

    @staticmethod
    async def process_transfer(info: TransferInfo) -> int:
        """전송 트랜잭션 처리

        Args:
            info: 전송 정보

        Returns:
            발송된 알림 수
        """
        notifications_sent = 0

        # FROM 지갑 알림 (항상)
        notifications_sent += await TransactionProcessor._notify_wallets(
            address=info.from_addr,
            direction="OUT",
            info=info,
            counterparty=info.counterparty_name or info.to_addr,
            check_incoming=False
        )

        # TO 지갑 알림 (스왑이 아닌 경우, incoming 체크)
        if not info.is_swap:
            notifications_sent += await TransactionProcessor._notify_wallets(
                address=info.to_addr,
                direction="IN",
                info=info,
                counterparty=info.counterparty_name or info.from_addr,
                check_incoming=True
            )

        return notifications_sent

    @staticmethod
    async def process_swap(
        from_addr: str,
        chain: str,
        swap_summary: str,
        amount_usd: float,
        tx_hash: str,
        dex_name: str = "DEX"
    ) -> int:
        """스왑 트랜잭션 처리

        Args:
            from_addr: 스왑 실행자 주소
            chain: 체인 코드
            swap_summary: 스왑 요약 (예: "0.5 ETH -> 1000 USDC")
            amount_usd: USD 가치
            tx_hash: 트랜잭션 해시
            dex_name: DEX 이름

        Returns:
            발송된 알림 수
        """
        info = TransferInfo(
            from_addr=from_addr,
            to_addr="",
            chain=chain,
            tx_type="DEX Swap",
            amount=swap_summary,
            amount_usd=amount_usd,
            tx_hash=tx_hash,
            is_swap=True,
            counterparty_name=dex_name
        )

        return await TransactionProcessor._notify_wallets(
            address=from_addr,
            direction="",
            info=info,
            counterparty=dex_name,
            check_incoming=False
        )

    @staticmethod
    async def _notify_wallets(
        address: str,
        direction: str,
        info: TransferInfo,
        counterparty: str,
        check_incoming: bool
    ) -> int:
        """지갑별 알림 발송

        Args:
            address: 확인할 지갑 주소
            direction: "IN" / "OUT" / ""
            info: 전송 정보
            counterparty: 상대방 주소/이름
            check_incoming: incoming_enabled 체크 여부

        Returns:
            발송된 알림 수
        """
        if not address:
            return 0

        wallets = await WalletCRUD.get_wallet_by_address(address.lower())
        notifications_sent = 0

        for wallet in wallets:
            # incoming 체크 (수신 알림인 경우)
            if check_incoming and not wallet.get("incoming_enabled"):
                logger.debug(f"[SKIP] {wallet['label']}: incoming disabled")
                continue

            # min_amount 체크 (None 대비 float 변환)
            min_amount = float(wallet.get("min_amount_usd") or 0)
            if info.amount_usd < min_amount:
                logger.debug(
                    f"[SKIP] {wallet['label']}: ${info.amount_usd:.2f} < ${min_amount:.2f} (min_amount)"
                )
                continue

            # 알림 발송
            logger.info(
                f"[PASS] {wallet['label']}: ${info.amount_usd:.2f} >= ${min_amount:.2f} "
                f"({direction or 'SWAP'} on {info.chain})"
            )

            await send_notification(
                user_id=wallet["user_id"],
                label=wallet["label"],
                chain=info.chain,
                tx_type=info.tx_type,
                direction=direction,
                amount=info.amount,
                amount_usd=info.amount_usd,
                counterparty=counterparty,
                tx_hash=info.tx_hash,
                is_swap=info.is_swap,
            )
            notifications_sent += 1

        return notifications_sent

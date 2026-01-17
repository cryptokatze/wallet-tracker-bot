"""CRUD 함수"""
from typing import Optional
from loguru import logger
from .models import get_db


class WalletCRUD:
    """지갑 CRUD 함수"""

    @staticmethod
    async def add_wallet(
        user_id: int,
        chain: str,
        address: str,
        label: str,
        stream_id: Optional[str] = None,
    ) -> int:
        """지갑 추가"""
        db = await get_db()
        try:
            cursor = await db.execute(
                """
                INSERT INTO wallets (user_id, chain, address, label, stream_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, chain.lower(), address.lower(), label, stream_id),
            )
            wallet_id = cursor.lastrowid

            # 기본 설정 추가
            await db.execute(
                """
                INSERT INTO wallet_settings (wallet_id) VALUES (?)
                """,
                (wallet_id,),
            )

            await db.commit()
            logger.info(f"Wallet added: {label} ({chain}:{address[:10]}...)")
            return wallet_id
        except Exception as e:
            logger.error(f"Failed to add wallet: {e}")
            raise

    @staticmethod
    async def get_wallets(user_id: int) -> list[dict]:
        """사용자의 지갑 목록 조회"""
        db = await get_db()
        cursor = await db.execute(
            """
            SELECT w.*, ws.incoming_enabled, ws.min_amount_usd
            FROM wallets w
            LEFT JOIN wallet_settings ws ON w.id = ws.wallet_id
            WHERE w.user_id = ?
            ORDER BY w.created_at DESC
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    async def get_wallet_by_label(user_id: int, label: str) -> Optional[dict]:
        """라벨로 지갑 조회"""
        db = await get_db()
        cursor = await db.execute(
            """
            SELECT w.*, ws.incoming_enabled, ws.min_amount_usd
            FROM wallets w
            LEFT JOIN wallet_settings ws ON w.id = ws.wallet_id
            WHERE w.user_id = ? AND w.label = ?
            """,
            (user_id, label),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    async def get_wallet_by_address(address: str) -> list[dict]:
        """주소로 지갑 조회 (알림 전송용)"""
        db = await get_db()
        cursor = await db.execute(
            """
            SELECT w.*, ws.incoming_enabled, ws.min_amount_usd
            FROM wallets w
            LEFT JOIN wallet_settings ws ON w.id = ws.wallet_id
            WHERE LOWER(w.address) = LOWER(?)
            """,
            (address,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    async def get_wallet_by_address_for_user(user_id: int, address: str) -> Optional[dict]:
        """특정 사용자의 주소로 지갑 조회 (중복 확인용)"""
        db = await get_db()
        cursor = await db.execute(
            """
            SELECT w.*, ws.incoming_enabled, ws.min_amount_usd
            FROM wallets w
            LEFT JOIN wallet_settings ws ON w.id = ws.wallet_id
            WHERE w.user_id = ? AND LOWER(w.address) = LOWER(?)
            """,
            (user_id, address),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    async def remove_wallet(user_id: int, label: str) -> bool:
        """지갑 삭제"""
        db = await get_db()
        cursor = await db.execute(
            """
            DELETE FROM wallets WHERE user_id = ? AND label = ?
            """,
            (user_id, label),
        )
        await db.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Wallet removed: {label}")
        return deleted

    @staticmethod
    async def update_stream_id(wallet_id: int, stream_id: str) -> bool:
        """스트림 ID 업데이트"""
        db = await get_db()
        await db.execute(
            """
            UPDATE wallets SET stream_id = ? WHERE id = ?
            """,
            (stream_id, wallet_id),
        )
        await db.commit()
        return True

    @staticmethod
    async def toggle_incoming(user_id: int, label: str) -> Optional[bool]:
        """incoming 알림 토글"""
        db = await get_db()

        # 현재 상태 조회
        wallet = await WalletCRUD.get_wallet_by_label(user_id, label)
        if not wallet:
            return None

        new_state = not wallet["incoming_enabled"]
        await db.execute(
            """
            UPDATE wallet_settings
            SET incoming_enabled = ?
            WHERE wallet_id = ?
            """,
            (int(new_state), wallet["id"]),
        )
        await db.commit()
        logger.info(f"Incoming toggled for {label}: {new_state}")
        return new_state

    @staticmethod
    async def set_min_amount(user_id: int, label: str, amount: float) -> bool:
        """최소 금액 필터 설정"""
        db = await get_db()

        wallet = await WalletCRUD.get_wallet_by_label(user_id, label)
        if not wallet:
            return False

        await db.execute(
            """
            UPDATE wallet_settings
            SET min_amount_usd = ?
            WHERE wallet_id = ?
            """,
            (amount, wallet["id"]),
        )
        await db.commit()
        logger.info(f"Min amount set for {label}: ${amount}")
        return True

"""SQLite 데이터베이스 모델"""
import aiosqlite
from config import settings
from loguru import logger

# DB 연결
_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """DB 연결 반환"""
    global _db
    if _db is None:
        _db = await aiosqlite.connect(settings.database_path)
        _db.row_factory = aiosqlite.Row
    return _db


async def init_db():
    """DB 테이블 초기화"""
    db = await get_db()

    # wallets 테이블: 추적할 지갑 목록
    await db.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chain TEXT NOT NULL,
            address TEXT NOT NULL,
            label TEXT NOT NULL,
            stream_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, label)
        )
    """)

    # settings 테이블: 지갑별 설정
    await db.execute("""
        CREATE TABLE IF NOT EXISTS wallet_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id INTEGER NOT NULL,
            incoming_enabled INTEGER DEFAULT 1,
            min_amount_usd REAL DEFAULT 0,
            FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE
        )
    """)

    # 인덱스 생성
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_wallets_user_id ON wallets(user_id)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_wallets_address ON wallets(address)
    """)

    await db.commit()
    logger.info("Database initialized successfully")


async def close_db():
    """DB 연결 종료"""
    global _db
    if _db:
        await _db.close()
        _db = None
        logger.info("Database connection closed")

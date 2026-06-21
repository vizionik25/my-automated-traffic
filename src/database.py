import sqlite3
from typing import List

class DatabaseManager:
    """Manages SQLite database connections, initialization, and basic table queries."""

    def __init__(self, db_path: str) -> None:
        """Initialize the DatabaseManager with the path to the database file."""
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a new SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def initialize(self) -> None:
        """Create database tables if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    description TEXT,
                    compliance_rules TEXT,
                    niche TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    offer_id INTEGER NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'paused',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blog_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    keyword TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content_markdown TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    published_url TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    script_text TEXT NOT NULL,
                    audio_path TEXT,
                    video_path TEXT,
                    status TEXT NOT NULL DEFAULT 'queued',
                    platform_urls TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    platform TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    thread_title_or_content TEXT,
                    reply_content TEXT,
                    status TEXT NOT NULL DEFAULT 'scraped',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform, thread_id)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    platform TEXT NOT NULL,
                    clicks INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    conversions INTEGER DEFAULT 0,
                    recorded_date DATE NOT NULL,
                    UNIQUE(campaign_id, platform, recorded_date)
                );
            """)
            conn.commit()

    def get_tables(self) -> List[str]:
        """Retrieve the list of user tables existing in the database (excluding internal tables)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            return [row[0] for row in cursor.fetchall()]

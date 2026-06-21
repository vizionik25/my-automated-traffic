import sqlite3
import pytest
from src.database import DatabaseManager

@pytest.fixture
def db(tmp_path):
    """Fixture to create, initialize, and return a temporary DatabaseManager instance."""
    db_path = tmp_path / "test.db"
    manager = DatabaseManager(str(db_path))
    manager.initialize()
    return manager

def test_db_initialization(db):
    """Verify that all required tables are successfully created upon initialization."""
    tables = db.get_tables()
    assert "offers" in tables
    assert "campaigns" in tables
    assert "blog_posts" in tables
    assert "video_assets" in tables
    assert "social_leads" in tables
    assert "analytics" in tables

def test_analytics_unique_constraint(db):
    """Verify that composite uniqueness is enforced on campaign_id, platform, and recorded_date."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        # Insert dummy offer
        cursor.execute("INSERT INTO offers (url, niche) VALUES ('http://test.com', 'dating')")
        offer_id = cursor.lastrowid
        
        # Insert dummy campaigns
        cursor.execute("INSERT INTO campaigns (offer_id, name) VALUES (?, 'campaign_1')", (offer_id,))
        c1_id = cursor.lastrowid
        cursor.execute("INSERT INTO campaigns (offer_id, name) VALUES (?, 'campaign_2')", (offer_id,))
        c2_id = cursor.lastrowid
        
        # Insert analytics for campaign 1, platform 'reddit', date '2026-06-21'
        cursor.execute("""
            INSERT INTO analytics (campaign_id, platform, clicks, recorded_date)
            VALUES (?, 'reddit', 10, '2026-06-21')
        """, (c1_id,))
        
        # Insert analytics for campaign 2, platform 'reddit', date '2026-06-21' (same date, different campaign)
        # This should SUCCEED
        cursor.execute("""
            INSERT INTO analytics (campaign_id, platform, clicks, recorded_date)
            VALUES (?, 'reddit', 20, '2026-06-21')
        """, (c2_id,))
        
        # Insert analytics for campaign 1, platform 'twitter', date '2026-06-21' (same date, same campaign, different platform)
        # This should SUCCEED
        cursor.execute("""
            INSERT INTO analytics (campaign_id, platform, clicks, recorded_date)
            VALUES (?, 'twitter', 30, '2026-06-21')
        """, (c1_id,))
        
        # Insert duplicate analytics for campaign 1, platform 'reddit', date '2026-06-21'
        # This should FAIL with sqlite3.IntegrityError
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO analytics (campaign_id, platform, clicks, recorded_date)
                VALUES (?, 'reddit', 40, '2026-06-21')
            """, (c1_id,))

def test_cascade_delete(db):
    """Verify that deleting an offer cascades to delete any related campaigns."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Insert dummy offer
        cursor.execute("INSERT INTO offers (url, niche) VALUES ('http://test.com', 'dating')")
        offer_id = cursor.lastrowid
        
        # Insert dummy campaign associated with the offer
        cursor.execute("INSERT INTO campaigns (offer_id, name) VALUES (?, 'dating_camp')", (offer_id,))
        campaign_id = cursor.lastrowid
        
        # Verify both exist initially
        cursor.execute("SELECT id FROM offers WHERE id = ?", (offer_id,))
        assert cursor.fetchone() is not None
        cursor.execute("SELECT id FROM campaigns WHERE id = ?", (campaign_id,))
        assert cursor.fetchone() is not None
        
        # Delete the offer
        cursor.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
        conn.commit()
        
        # Verify the campaign was automatically deleted by CASCADE
        cursor.execute("SELECT id FROM campaigns WHERE id = ?", (campaign_id,))
        assert cursor.fetchone() is None

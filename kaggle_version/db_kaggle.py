"""
Database operations for MedMon using SQLite (Kaggle Compatible)
"""
import sqlite3
from datetime import datetime
from contextlib import contextmanager
import os

DATABASE_NAME = 'medmon.db'

@contextmanager
def get_connection():
    """Context manager for database connections."""
    # check_same_thread=False is needed for Streamlit's threading model with SQLite
    conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Access columns by name
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize database and create tables if not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Keywords table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Articles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword_id INTEGER,
                title TEXT,
                url TEXT,
                publisher TEXT,
                publish_date TIMESTAMP,
                content TEXT,
                sentiment_label TEXT,
                sentiment_score REAL,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
            )
        """)
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_keyword ON articles(keyword_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON articles(publish_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment ON articles(sentiment_label)")
        
        # Scrape history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword_id INTEGER,
                total_found INTEGER,
                total_success INTEGER,
                positive_count INTEGER,
                negative_count INTEGER,
                neutral_count INTEGER,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    
    print("[DB] Database initialized successfully.")

def add_keyword(keyword):
    """Add a new keyword to track."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO keywords (keyword) VALUES (?)",
            (keyword,)
        )
        conn.commit()
        
        # Get the keyword ID
        cursor.execute("SELECT id FROM keywords WHERE keyword = ?", (keyword,))
        result = cursor.fetchone()
        return result['id'] if result else None

def get_keywords():
    """Get all active keywords."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, keyword FROM keywords WHERE is_active = 1 ORDER BY created_at DESC")
        return cursor.fetchall()

def save_article(article, keyword_id):
    """Save a single article to the database. Returns article_id if new, 'duplicate' if exists, None if error."""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Check for duplicate URL
        cursor.execute("SELECT id FROM articles WHERE url = ?", (article.get('url'),))
        if cursor.fetchone():
            return "duplicate"  # Already exists - return marker
        
        # Parse publish date - handle multiple formats
        pub_date = article.get('publish_date')
        if pub_date:
            # SQLite stores dates as strings/timestamps mainly, let's keep it simple or convert to ISO string
            if isinstance(pub_date, datetime):
                pub_date = pub_date.isoformat()
            else:
                try:
                    # Try to normalize string dates to ISO if possible, otherwise store as is
                    from dateutil import parser as date_parser
                    dt = date_parser.parse(str(pub_date))
                    pub_date = dt.isoformat()
                except:
                    pass
        
        cursor.execute("""
            INSERT INTO articles (keyword_id, title, url, publisher, publish_date, content, sentiment_label, sentiment_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            keyword_id,
            article.get('title'),
            article.get('url'),
            article.get('publisher'),
            pub_date,
            article.get('text'),
            article.get('sentiment_label'),
            article.get('sentiment_score')
        ))
        conn.commit()
        return cursor.lastrowid

def save_scrape_history(keyword_id, total_found, total_success, pos, neg, neu):
    """Save scrape history for analytics."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scrape_history (keyword_id, total_found, total_success, positive_count, negative_count, neutral_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (keyword_id, total_found, total_success, pos, neg, neu))
        conn.commit()

def get_articles(keyword_id=None, date_from=None, date_to=None, limit=100):
    """Get articles with optional filters."""
    query = "SELECT a.*, k.keyword FROM articles a JOIN keywords k ON a.keyword_id = k.id WHERE 1=1"
    params = []
    
    if keyword_id:
        query += " AND a.keyword_id = ?"
        params.append(keyword_id)
    
    if date_from:
        query += " AND a.publish_date >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND a.publish_date <= ?"
        params.append(date_to)
    
    query += " ORDER BY a.scraped_at DESC LIMIT ?"
    params.append(limit)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

def get_trend_data(keyword_id=None, days=30):
    """Get daily article count and sentiment for trend analysis."""
    # SQLite syntax for date manipulation
    query = """
        SELECT 
            date(scraped_at) as date,
            COUNT(*) as total,
            SUM(CASE WHEN sentiment_label = 'Positive' THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN sentiment_label = 'Negative' THEN 1 ELSE 0 END) as negative,
            SUM(CASE WHEN sentiment_label = 'Neutral' THEN 1 ELSE 0 END) as neutral
        FROM articles
        WHERE scraped_at >= date('now', '-' || ? || ' days')
    """
    params = [str(days)]
    
    if keyword_id:
        query += " AND keyword_id = ?"
        params.append(keyword_id)
    
    query += " GROUP BY date(scraped_at) ORDER BY date"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

def get_keyword_comparison():
    """Get article count per keyword for comparison."""
    query = """
        SELECT 
            k.keyword,
            COUNT(a.id) as total_articles,
            SUM(CASE WHEN a.sentiment_label = 'Positive' THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN a.sentiment_label = 'Negative' THEN 1 ELSE 0 END) as negative
        FROM keywords k
        LEFT JOIN articles a ON k.id = a.keyword_id
        WHERE k.is_active = 1
        GROUP BY k.id, k.keyword
        ORDER BY total_articles DESC
    """
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

def delete_keyword(keyword_id):
    """Delete a keyword and all its articles."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))
        conn.commit()

def clear_all_articles():
    """Clear all articles from database (for re-scraping with fixed logic)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scrape_history")
        cursor.execute("DELETE FROM articles")
        conn.commit()
    print("[DB] All articles cleared. Ready for fresh scrape.")

# Initialize database on import (only creates if not exists)
if __name__ == "__main__":
    init_database()
    print("[DB] Database setup complete.")

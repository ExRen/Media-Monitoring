# """
# Database operations for MedMon using MySQL (Laragon)
# """
# import pymysql
# from datetime import datetime
# from contextlib import contextmanager

# # Database Configuration (Laragon defaults)
# DB_CONFIG = {
#     'host': 'localhost',
#     'port': 3306,
#     'user': 'root',
#     'password': '',  # Laragon default is empty
#     'charset': 'utf8mb4',
#     'cursorclass': pymysql.cursors.DictCursor
# }

# DATABASE_NAME = 'medmon'

# @contextmanager
# def get_connection(use_db=True):
#     """Context manager for database connections."""
#     config = DB_CONFIG.copy()
#     if use_db:
#         config['database'] = DATABASE_NAME
    
#     conn = pymysql.connect(**config)
#     try:
#         yield conn
#     finally:
#         conn.close()

# def init_database():
#     """Initialize database and create tables if not exist."""
#     # Create database
#     with get_connection(use_db=False) as conn:
#         with conn.cursor() as cursor:
#             cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
#         conn.commit()
    
#     # Create tables
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             # Keywords table
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS keywords (
#                     id INT AUTO_INCREMENT PRIMARY KEY,
#                     keyword VARCHAR(255) UNIQUE NOT NULL,
#                     tone_positive TEXT,
#                     tone_negative TEXT,
#                     is_active BOOLEAN DEFAULT TRUE,
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 )
#             """)
            
#             # Users table
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS users (
#                     id INT AUTO_INCREMENT PRIMARY KEY,
#                     username VARCHAR(255) UNIQUE NOT NULL,
#                     password_hash VARCHAR(255) NOT NULL,
#                     role VARCHAR(50) NOT NULL,
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 )
#             """)
            
#             # Articles table
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS articles (
#                     id INT AUTO_INCREMENT PRIMARY KEY,
#                     keyword_id INT,
#                     title TEXT,
#                     url TEXT,
#                     publisher VARCHAR(255),
#                     publish_date DATETIME,
#                     content LONGTEXT,
#                     sentiment_label VARCHAR(20),
#                     sentiment_score FLOAT,
#                     status VARCHAR(20) DEFAULT 'pending',
#                     proof_file_path TEXT,
#                     is_internal BOOLEAN DEFAULT FALSE,
#                     scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                     FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE,
#                     INDEX idx_keyword (keyword_id),
#                     INDEX idx_date (publish_date),
#                     INDEX idx_sentiment (sentiment_label),
#                     INDEX idx_status (status)
#                 )
#             """)
            
#             # Scrape history table
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS scrape_history (
#                     id INT AUTO_INCREMENT PRIMARY KEY,
#                     keyword_id INT,
#                     total_found INT,
#                     total_success INT,
#                     positive_count INT,
#                     negative_count INT,
#                     neutral_count INT,
#                     scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                     FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
#                 )
#             """)
#         conn.commit()
    
#     print("[DB] Database initialized successfully.")

# def add_keyword(keyword):
#     """Add a new keyword to track."""
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute(
#                 "INSERT IGNORE INTO keywords (keyword) VALUES (%s)",
#                 (keyword,)
#             )
#         conn.commit()
        
#         # Get the keyword ID
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT id FROM keywords WHERE keyword = %s", (keyword,))
#             result = cursor.fetchone()
#             return result['id'] if result else None

# def get_keywords():
#     """Get all active keywords with custom tones."""
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT id, keyword, tone_positive, tone_negative FROM keywords WHERE is_active = TRUE ORDER BY created_at DESC")
#             return cursor.fetchall()
            
# def update_keyword_tones(keyword_id, pos_tones, neg_tones):
#     """Update custom tones for a keyword."""
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute("UPDATE keywords SET tone_positive = %s, tone_negative = %s WHERE id = %s", 
#                            (pos_tones, neg_tones, keyword_id))
#         conn.commit()

# def save_article(article, keyword_id):
#     """Save a single article to the database. Returns article_id if new, 'duplicate' if exists, None if error."""
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             # Check for duplicate URL
#             cursor.execute("SELECT id FROM articles WHERE url = %s", (article.get('url'),))
#             if cursor.fetchone():
#                 return "duplicate"  # Already exists - return marker
            
#             # Parse publish date - handle multiple formats
#             pub_date = article.get('publish_date')
#             if pub_date and not isinstance(pub_date, datetime):
#                 pub_date_str = str(pub_date)
#                 try:
#                     # Try ISO format first
#                     pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
#                 except:
#                     try:
#                         # Try RFC 2822 format (Google News format: "Mon, 06 Jan 2026 07:00:00 GMT")
#                         from email.utils import parsedate_to_datetime
#                         pub_date = parsedate_to_datetime(pub_date_str)
#                     except:
#                         try:
#                             # Try common format "Jan 6, 2026"
#                             from dateutil import parser as date_parser
#                             pub_date = date_parser.parse(pub_date_str)
#                         except:
#                             pub_date = None
            
#             cursor.execute("""
#                 INSERT INTO articles (keyword_id, title, url, publisher, publish_date, content, sentiment_label, sentiment_score, status)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
#             """, (
#                 keyword_id,
#                 article.get('title'),
#                 article.get('url'),
#                 article.get('publisher'),
#                 pub_date,
#                 article.get('text'),
#                 article.get('sentiment_label'),
#                 article.get('sentiment_score')
#             ))
#         conn.commit()
#         return cursor.lastrowid
        
# def get_pending_articles():
#     """Get all articles waiting for manual review."""
#     query = "SELECT a.*, k.keyword FROM articles a JOIN keywords k ON a.keyword_id = k.id WHERE a.status = 'pending' ORDER BY a.scraped_at DESC"
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute(query)
#             return cursor.fetchall()
            
# def update_article_status(article_id, status, new_tone=None, proof_path=None, is_internal=False):
#     """Approve/edit an article."""
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             if new_tone:
#                 cursor.execute("""
#                     UPDATE articles 
#                     SET status = %s, sentiment_label = %s, proof_file_path = %s, is_internal = %s 
#                     WHERE id = %s
#                 """, (status, new_tone, proof_path, is_internal, article_id))
#             else:
#                 cursor.execute("""
#                     UPDATE articles 
#                     SET status = %s, proof_file_path = %s, is_internal = %s 
#                     WHERE id = %s
#                 """, (status, proof_path, is_internal, article_id))
#         conn.commit()

# # User Management Functions
# import hashlib

# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# def create_user(username, password, role):
#     try:
#         with get_connection() as conn:
#             with conn.cursor() as cursor:
#                 cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
#                                (username, hash_password(password), role))
#             conn.commit()
#             return True
#     except:
#         return False

# def authenticate_user(username, password):
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT id, username, role FROM users WHERE username = %s AND password_hash = %s", 
#                            (username, hash_password(password)))
#             return cursor.fetchone()

# def get_all_users():
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT id, username, role, created_at FROM users")
#             return cursor.fetchall()

# def save_scrape_history(keyword_id, total_found, total_success, pos, neg, neu):
#     """Save scrape history for analytics."""
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute("""
#                 INSERT INTO scrape_history (keyword_id, total_found, total_success, positive_count, negative_count, neutral_count)
#                 VALUES (%s, %s, %s, %s, %s, %s)
#             """, (keyword_id, total_found, total_success, pos, neg, neu))
#         conn.commit()

# def get_articles(keyword_id=None, date_from=None, date_to=None, limit=100):
#     """Get articles with optional filters."""
#     query = "SELECT a.*, k.keyword FROM articles a JOIN keywords k ON a.keyword_id = k.id WHERE a.status = 'published'"
#     params = []
    
#     if keyword_id:
#         query += " AND a.keyword_id = %s"
#         params.append(keyword_id)
    
#     if date_from:
#         query += " AND a.publish_date >= %s"
#         params.append(date_from)
    
#     if date_to:
#         query += " AND a.publish_date <= %s"
#         params.append(date_to)
    
#     query += " ORDER BY a.scraped_at DESC LIMIT %s"
#     params.append(limit)
    
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute(query, params)
#             return cursor.fetchall()

# def get_trend_data(keyword_id=None, days=30):
#     """Get daily article count and sentiment for trend analysis."""
#     query = """
#         SELECT 
#             DATE(scraped_at) as date,
#             COUNT(*) as total,
#             SUM(CASE WHEN sentiment_label = 'Positive' THEN 1 ELSE 0 END) as positive,
#             SUM(CASE WHEN sentiment_label = 'Negative' THEN 1 ELSE 0 END) as negative,
#             SUM(CASE WHEN sentiment_label = 'Neutral' THEN 1 ELSE 0 END) as neutral
#         FROM articles
#         WHERE scraped_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY) AND status = 'published'
#     """
#     params = [days]
    
#     if keyword_id:
#         query += " AND keyword_id = %s"
#         params.append(keyword_id)
    
#     query += " GROUP BY DATE(scraped_at) ORDER BY date"
    
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute(query, params)
#             return cursor.fetchall()

# def get_keyword_comparison():
#     """Get article count per keyword for comparison."""
#     query = """
#         SELECT 
#             k.keyword,
#             COUNT(a.id) as total_articles,
#             SUM(CASE WHEN a.sentiment_label = 'Positive' THEN 1 ELSE 0 END) as positive,
#             SUM(CASE WHEN a.sentiment_label = 'Negative' THEN 1 ELSE 0 END) as negative
#         FROM keywords k
#         LEFT JOIN articles a ON k.id = a.keyword_id AND a.status = 'published'
#         WHERE k.is_active = TRUE
#         GROUP BY k.id, k.keyword
#         ORDER BY total_articles DESC
#     """
    
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute(query)
#             return cursor.fetchall()

# def delete_keyword(keyword_id):
#     """Delete a keyword and all its articles."""
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute("DELETE FROM keywords WHERE id = %s", (keyword_id,))
#         conn.commit()

# def clear_all_articles():
#     """Clear all articles from database (for re-scraping with fixed logic)."""
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute("DELETE FROM scrape_history")
#             cursor.execute("DELETE FROM articles")
#         conn.commit()
#     print("[DB] All articles cleared. Ready for fresh scrape.")

# # Initialize database on import (only creates if not exists)
# if __name__ == "__main__":
#     init_database()
#     print("[DB] Database setup complete.")

"""
Database operations for MedMon using MySQL (Laragon)
"""
import os
import pymysql
from datetime import datetime
from contextlib import contextmanager

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Database Configuration (dari environment variables)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

DATABASE_NAME = os.getenv('DB_NAME', 'medmon')

@contextmanager
def get_connection(use_db=True):
    """Context manager for database connections."""
    config = DB_CONFIG.copy()
    if use_db:
        config['database'] = DATABASE_NAME
    
    conn = pymysql.connect(**config)
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize database and create tables if not exist."""
    # Create database
    with get_connection(use_db=False) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
    
    # Create tables
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Keywords table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keywords (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    keyword VARCHAR(255) UNIQUE NOT NULL,
                    tone_positive TEXT,
                    tone_negative TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Articles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    keyword_id INT,
                    title TEXT,
                    url TEXT,
                    publisher VARCHAR(255),
                    publish_date DATETIME,
                    content LONGTEXT,
                    sentiment_label VARCHAR(20),
                    sentiment_score FLOAT,
                    status VARCHAR(20) DEFAULT 'pending',
                    proof_file_path TEXT,
                    is_internal BOOLEAN DEFAULT FALSE,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE,
                    INDEX idx_keyword (keyword_id),
                    INDEX idx_date (publish_date),
                    INDEX idx_sentiment (sentiment_label),
                    INDEX idx_status (status)
                )
            """)
            
            # Scrape history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    keyword_id INT,
                    total_found INT,
                    total_success INT,
                    positive_count INT,
                    negative_count INT,
                    neutral_count INT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
                )
            """)
        conn.commit()
    
    print("[DB] Database initialized successfully.")

def add_keyword(keyword):
    """Add a new keyword to track."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT IGNORE INTO keywords (keyword) VALUES (%s)",
                (keyword,)
            )
        conn.commit()
        
        # Get the keyword ID
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM keywords WHERE keyword = %s", (keyword,))
            result = cursor.fetchone()
            return result['id'] if result else None

def get_keywords():
    """Get all active keywords with custom tones."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, keyword, tone_positive, tone_negative FROM keywords WHERE is_active = TRUE ORDER BY created_at DESC")
            return cursor.fetchall()
            
def update_keyword_tones(keyword_id, pos_tones, neg_tones):
    """Update custom tones for a keyword."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE keywords SET tone_positive = %s, tone_negative = %s WHERE id = %s", 
                           (pos_tones, neg_tones, keyword_id))
        conn.commit()

def save_article(article, keyword_id):
    """Save a single article to the database. Returns article_id if new, 'duplicate' if exists, None if error."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Check for duplicate URL
            cursor.execute("SELECT id FROM articles WHERE url = %s", (article.get('url'),))
            if cursor.fetchone():
                return "duplicate"  # Already exists - return marker
            
            # Parse publish date - handle multiple formats
            pub_date = article.get('publish_date')
            if pub_date and not isinstance(pub_date, datetime):
                pub_date_str = str(pub_date)
                try:
                    # Try ISO format first
                    pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                except:
                    try:
                        # Try RFC 2822 format (Google News format: "Mon, 06 Jan 2026 07:00:00 GMT")
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(pub_date_str)
                    except:
                        try:
                            # Try common format "Jan 6, 2026"
                            from dateutil import parser as date_parser
                            pub_date = date_parser.parse(pub_date_str)
                        except:
                            pub_date = None
            
            cursor.execute("""
                INSERT INTO articles (keyword_id, title, url, publisher, publish_date, content, sentiment_label, sentiment_score, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
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
        
def get_pending_articles():
    """Get all articles waiting for manual review."""
    query = "SELECT a.*, k.keyword FROM articles a JOIN keywords k ON a.keyword_id = k.id WHERE a.status = 'pending' ORDER BY a.scraped_at DESC"
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
            
def update_article_status(article_id, status, new_tone=None, proof_path=None, is_internal=False):
    """Approve/edit an article."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            if new_tone:
                cursor.execute("""
                    UPDATE articles 
                    SET status = %s, sentiment_label = %s, proof_file_path = %s, is_internal = %s 
                    WHERE id = %s
                """, (status, new_tone, proof_path, is_internal, article_id))
            else:
                cursor.execute("""
                    UPDATE articles 
                    SET status = %s, proof_file_path = %s, is_internal = %s 
                    WHERE id = %s
                """, (status, proof_path, is_internal, article_id))
        conn.commit()

# User Management Functions
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, role):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                               (username, hash_password(password), role))
            conn.commit()
            return True
    except:
        return False

def authenticate_user(username, password):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, role FROM users WHERE username = %s AND password_hash = %s", 
                           (username, hash_password(password)))
            return cursor.fetchone()

def get_all_users():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, role, created_at FROM users")
            return cursor.fetchall()

def save_scrape_history(keyword_id, total_found, total_success, pos, neg, neu):
    """Save scrape history for analytics."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO scrape_history (keyword_id, total_found, total_success, positive_count, negative_count, neutral_count)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (keyword_id, total_found, total_success, pos, neg, neu))
        conn.commit()

def get_articles(keyword_id=None, date_from=None, date_to=None, limit=100):
    """Get articles with optional filters."""
    query = "SELECT a.*, k.keyword FROM articles a JOIN keywords k ON a.keyword_id = k.id WHERE a.status = 'published'"
    params = []
    
    if keyword_id:
        query += " AND a.keyword_id = %s"
        params.append(keyword_id)
    
    if date_from:
        query += " AND a.publish_date >= %s"
        params.append(date_from)
    
    if date_to:
        query += " AND a.publish_date <= %s"
        params.append(date_to)
    
    query += " ORDER BY a.scraped_at DESC LIMIT %s"
    params.append(limit)
    
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

def get_trend_data(keyword_id=None, days=30):
    """Get daily article count and sentiment for trend analysis."""
    query = """
        SELECT 
            DATE(scraped_at) as date,
            COUNT(*) as total,
            SUM(CASE WHEN sentiment_label = 'Positive' THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN sentiment_label = 'Negative' THEN 1 ELSE 0 END) as negative,
            SUM(CASE WHEN sentiment_label = 'Neutral' THEN 1 ELSE 0 END) as neutral
        FROM articles
        WHERE scraped_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY) AND status = 'published'
    """
    params = [days]
    
    if keyword_id:
        query += " AND keyword_id = %s"
        params.append(keyword_id)
    
    query += " GROUP BY DATE(scraped_at) ORDER BY date"
    
    with get_connection() as conn:
        with conn.cursor() as cursor:
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
        LEFT JOIN articles a ON k.id = a.keyword_id AND a.status = 'published'
        WHERE k.is_active = TRUE
        GROUP BY k.id, k.keyword
        ORDER BY total_articles DESC
    """
    
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

def delete_keyword(keyword_id):
    """Delete a keyword and all its articles."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM keywords WHERE id = %s", (keyword_id,))
        conn.commit()

def clear_all_articles():
    """Clear all articles from database (for re-scraping with fixed logic)."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM scrape_history")
            cursor.execute("DELETE FROM articles")
        conn.commit()
    print("[DB] All articles cleared. Ready for fresh scrape.")

def get_articles_pending_sentiment(limit=100):
    """
    Ambil artikel yang belum dianalisis sentimen (sentiment_label = 'Pending').
    Dipanggil oleh medmon.run_batch_sentiment() untuk batch processing.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, content
                FROM articles
                WHERE sentiment_label = 'Pending'
                ORDER BY scraped_at DESC
                LIMIT %s
            """, (limit,))
            return cursor.fetchall()

def update_article_sentiment(article_id, score, label):
    """
    Update sentiment sebuah artikel setelah batch analysis.
    Dipanggil oleh medmon.run_batch_sentiment() untuk setiap artikel.
    Jika score=None, hanya update label (koreksi manual tanpa mengubah score).
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            if score is not None:
                cursor.execute(
                    "UPDATE articles SET sentiment_score = %s, sentiment_label = %s WHERE id = %s",
                    (score, label, article_id)
                )
            else:
                cursor.execute(
                    "UPDATE articles SET sentiment_label = %s WHERE id = %s",
                    (label, article_id)
                )
        conn.commit()

# Initialize database on import (only creates if not exists)
if __name__ == "__main__":
    init_database()
    print("[DB] Database setup complete.")
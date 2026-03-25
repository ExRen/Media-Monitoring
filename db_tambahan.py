"""
db_tambahan.py
==============
Fungsi-fungsi database BARU yang perlu ditambahkan ke db.py Anda
agar seluruh fitur MONITOR v4.0 dapat berjalan.

CARA PENGGUNAAN:
  1. Buka db.py Anda.
  2. Copy-paste seluruh isi file ini ke bagian bawah db.py.
  3. Pastikan variabel koneksi database (misalnya `get_connection()`) 
     sudah tersedia dan konsisten dengan kode db.py Anda yang ada.

ASUMSI:
  - Anda menggunakan MySQL (misalnya via Laragon / XAMPP).
  - Fungsi `get_connection()` sudah tersedia di db.py Anda
    dan mengembalikan koneksi MySQL (pymysql / mysql-connector).
  - Jika Anda menggunakan SQLite, ganti sintaks AUTO_INCREMENT 
    dengan AUTOINCREMENT, dan hapus `CHARACTER SET utf8mb4`.
"""

# ─── Contoh get_connection jika belum ada di db.py ────────────────────────────
# import pymysql
# def get_connection():
#     return pymysql.connect(
#         host="localhost", user="root", password="",
#         database="medmon_db", charset="utf8mb4",
#         cursorclass=pymysql.cursors.DictCursor
#     )
# ──────────────────────────────────────────────────────────────────────────────


# ==============================================================================
# INISIALISASI TABEL BARU
# ==============================================================================

def init_auth_tables():
    """
    Buat tabel `users` jika belum ada.
    Default admin: username=admin, password dari env var DEFAULT_ADMIN_PASSWORD.
    """
    import hashlib
    import os
    default_pw = os.getenv("DEFAULT_ADMIN_PASSWORD", "changeme")
    admin_hash = hashlib.sha256(default_pw.encode()).hexdigest()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id         INT AUTO_INCREMENT PRIMARY KEY,
                    username   VARCHAR(100) UNIQUE NOT NULL,
                    password   VARCHAR(256) NOT NULL,
                    role       VARCHAR(50)  NOT NULL DEFAULT 'level_2',
                    full_name  VARCHAR(200),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4;
            """)
            # Sisipkan admin default jika tabel masih kosong
            cur.execute("SELECT COUNT(*) AS cnt FROM users")
            row = cur.fetchone()
            cnt = row["cnt"] if isinstance(row, dict) else row[0]
            if cnt == 0:
                cur.execute(
                    "INSERT INTO users (username, password, role, full_name) VALUES (%s,%s,%s,%s)",
                    ("admin", admin_hash, "super_user", "Administrator"),
                )
        conn.commit()
    finally:
        conn.close()


def init_tone_keyword_tables():
    """Buat tabel `tone_keywords` jika belum ada."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tone_keywords (
                    id         INT AUTO_INCREMENT PRIMARY KEY,
                    word       VARCHAR(200) NOT NULL,
                    tone_type  VARCHAR(20)  NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_word_tone (word, tone_type)
                ) CHARACTER SET utf8mb4;
            """)
        conn.commit()
    finally:
        conn.close()


def init_article_meta_columns():
    """
    Tambahkan kolom-kolom baru ke tabel `articles` jika belum ada.
    Panggil fungsi ini sekali saja, misalnya dari init_database().
    """
    new_cols = [
        ("media_category", "VARCHAR(200) DEFAULT NULL"),
        ("source_type",    "VARCHAR(50)  DEFAULT NULL"),
        ("content_type",   "VARCHAR(50)  DEFAULT NULL"),
        ("reviewed_by",    "VARCHAR(100) DEFAULT NULL"),
        ("reviewed_at",    "DATETIME DEFAULT NULL"),
    ]
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for col_name, col_def in new_cols:
                try:
                    cur.execute(f"ALTER TABLE articles ADD COLUMN {col_name} {col_def}")
                    conn.commit()
                except Exception:
                    # Kolom sudah ada, abaikan error
                    conn.rollback()
    finally:
        conn.close()


def init_attachments_table():
    """Buat tabel `article_attachments` jika belum ada."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS article_attachments (
                    id         INT AUTO_INCREMENT PRIMARY KEY,
                    article_id INT NOT NULL,
                    filename   VARCHAR(300),
                    file_data  LONGBLOB,
                    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4;
            """)
        conn.commit()
    finally:
        conn.close()


# ==============================================================================
# USER MANAGEMENT
# ==============================================================================

def authenticate_user(username: str, password_hash: str):
    """
    Verifikasi login.
    Return dict user jika berhasil, None jika gagal.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, full_name, role FROM users WHERE username=%s AND password=%s",
                (username, password_hash),
            )
            return cur.fetchone()  # None jika tidak ditemukan
    finally:
        conn.close()


def get_users():
    """Return list semua user (tanpa password)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, full_name, role, created_at FROM users ORDER BY id")
            return cur.fetchall()
    finally:
        conn.close()


def add_user(username: str, password_hash: str, role: str, full_name: str):
    """
    Tambah user baru.
    Return id user baru, atau None jika username sudah ada.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (%s,%s,%s,%s)",
                (username, password_hash, role, full_name),
            )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        return None
    finally:
        conn.close()


def delete_user(user_id: int) -> bool:
    """Hapus user berdasarkan ID. Return True jika berhasil."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id=%s AND username != 'admin'", (user_id,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def update_user_password(user_id: int, new_hash: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET password=%s WHERE id=%s", (new_hash, user_id))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


# ==============================================================================
# TONE KEYWORDS
# ==============================================================================

def get_tone_keywords():
    """Return list dict {id, word, tone_type} dari tabel tone_keywords."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, word, tone_type FROM tone_keywords ORDER BY tone_type, word")
            return cur.fetchall()
    finally:
        conn.close()


def add_tone_keyword(word: str, tone_type: str):
    """
    Tambah keyword tone.
    Return id baru, atau None jika duplikat/gagal.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT IGNORE INTO tone_keywords (word, tone_type) VALUES (%s,%s)",
                (word.lower().strip(), tone_type),
            )
        conn.commit()
        return cur.lastrowid if cur.lastrowid else None
    except Exception:
        conn.rollback()
        return None
    finally:
        conn.close()


def delete_tone_keyword(kw_id: int) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tone_keywords WHERE id=%s", (kw_id,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


# ==============================================================================
# UPDATE ARTIKEL
# ==============================================================================

def update_article_tone(article_id: int, tone: str) -> bool:
    """
    Override tone (sentiment_label) sebuah artikel secara manual.
    tone: 'Positive' | 'Negative' | 'Neutral'
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE articles SET sentiment_label=%s WHERE id=%s",
                (tone, article_id),
            )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def update_article_meta(article_id: int, media_category: str,
                         source_type: str, content_type: str) -> bool:
    """
    Perbarui kolom tambahan artikel: kategori media (24 tier), 
    sumber (internal/eksternal), dan tipe konten (berita/video).
    Pastikan sudah memanggil init_article_meta_columns() terlebih dahulu.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE articles
                   SET media_category=%s, source_type=%s, content_type=%s,
                       reviewed_at=NOW()
                   WHERE id=%s""",
                (media_category, source_type, content_type, article_id),
            )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def save_attachment(article_id: int, filename: str, file_bytes: bytes) -> bool:
    """
    Simpan file bukti pemberitaan (PDF/gambar) ke tabel article_attachments.
    Pastikan sudah memanggil init_attachments_table() terlebih dahulu.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO article_attachments (article_id, filename, file_data)
                   VALUES (%s, %s, %s)""",
                (article_id, filename, file_bytes),
            )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


# ==============================================================================
# CATATAN INTEGRASI
# ==============================================================================
# Setelah menambahkan semua fungsi di atas ke db.py, panggil fungsi inisialisasi
# di dalam fungsi init_database() yang sudah ada:
#
#   def init_database():
#       # ... kode yang sudah ada ...
#       init_auth_tables()
#       init_tone_keyword_tables()
#       init_article_meta_columns()
#       init_attachments_table()
#
# Dengan demikian semua tabel baru akan otomatis dibuat saat aplikasi pertama kali
# dijalankan tanpa perlu menjalankan skrip SQL secara terpisah.
# ==============================================================================

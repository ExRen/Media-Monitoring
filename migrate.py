import os
import db
import pymysql

def migrate():
    print("Starting migration...")
    with db.get_connection() as conn:
        with conn.cursor() as cursor:
            # Articles
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN status VARCHAR(20) DEFAULT 'published'")
                print("Added status column.")
            except Exception as e:
                print("status error:", e)
                
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN proof_file_path TEXT")
                print("Added proof_file_path column.")
            except Exception as e:
                pass
                
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN is_internal BOOLEAN DEFAULT FALSE")
                print("Added is_internal column.")
            except Exception as e:
                pass
                
            # Keywords
            try:
                cursor.execute("ALTER TABLE keywords ADD COLUMN tone_positive TEXT")
                print("Added tone_positive column.")
            except Exception as e:
                pass
                
            try:
                cursor.execute("ALTER TABLE keywords ADD COLUMN tone_negative TEXT")
                print("Added tone_negative column.")
            except Exception as e:
                pass

        conn.commit()
    print("Migration complete!")
    
    print("Adding default admin user...")
    default_pw = os.getenv("DEFAULT_ADMIN_PASSWORD", "changeme")
    res = db.create_user("admin", default_pw, "Super User")
    if res:
        print("Admin user created.")
    else:
        print("Admin user might already exist.")

if __name__ == "__main__":
    migrate()

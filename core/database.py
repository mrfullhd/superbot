import sqlite3
import json
from datetime import datetime
from pathlib import Path

class Database:
    def __init__(self, db_path="data/database.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_tables()
    
    def init_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_date TEXT,
                is_banned INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                settings TEXT DEFAULT '{}'
            );
            
            CREATE TABLE IF NOT EXISTS tokens (
                user_id INTEGER PRIMARY KEY,
                token_data TEXT NOT NULL,
                drive_email TEXT,
                added_date TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                source TEXT,
                output TEXT,
                file_size INTEGER,
                status TEXT,
                date TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                url TEXT,
                file_name TEXT,
                status TEXT DEFAULT 'pending',
                progress REAL DEFAULT 0,
                start_date TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            
            CREATE TABLE IF NOT EXISTS cookies (
                user_id INTEGER PRIMARY KEY,
                cookies_data TEXT,
                added_date TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            
            CREATE TABLE IF NOT EXISTS stats (
                user_id INTEGER PRIMARY KEY,
                total_downloads INTEGER DEFAULT 0,
                total_size INTEGER DEFAULT 0,
                youtube_downloads INTEGER DEFAULT 0,
                direct_downloads INTEGER DEFAULT 0,
                uploads INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
        """)
        self.conn.commit()
    
    def add_user(self, user_id, username=None, first_name=None):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, joined_date) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, now)
        )
        self.conn.execute(
            "INSERT OR IGNORE INTO stats (user_id) VALUES (?)",
            (user_id,)
        )
        self.conn.commit()
    
    def is_banned(self, user_id):
        row = self.conn.execute("SELECT is_banned FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row and row["is_banned"] == 1
    
    def ban_user(self, user_id):
        self.conn.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
        self.conn.commit()
    
    def unban_user(self, user_id):
        self.conn.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
        self.conn.commit()
    
    def get_all_users(self):
        return self.conn.execute("SELECT * FROM users").fetchall()
    
    def user_count(self):
        return self.conn.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
    
    def save_token(self, user_id, token_data, drive_email):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(
            "INSERT OR REPLACE INTO tokens (user_id, token_data, drive_email, added_date) VALUES (?, ?, ?, ?)",
            (user_id, json.dumps(token_data), drive_email, now)
        )
        self.conn.commit()
    
    def get_token(self, user_id):
        row = self.conn.execute("SELECT * FROM tokens WHERE user_id=?", (user_id,)).fetchone()
        return json.loads(row["token_data"]) if row else None
    
    def delete_token(self, user_id):
        self.conn.execute("DELETE FROM tokens WHERE user_id=?", (user_id,))
        self.conn.commit()
    
    def is_authenticated(self, user_id):
        row = self.conn.execute("SELECT 1 FROM tokens WHERE user_id=?", (user_id,)).fetchone()
        return row is not None
    
    def save_cookies(self, user_id, cookies_data):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(
            "INSERT OR REPLACE INTO cookies (user_id, cookies_data, added_date) VALUES (?, ?, ?)",
            (user_id, cookies_data, now)
        )
        self.conn.commit()
    
    def get_cookies(self, user_id):
        row = self.conn.execute("SELECT cookies_data FROM cookies WHERE user_id=?", (user_id,)).fetchone()
        return row["cookies_data"] if row else None
    
    def add_history(self, user_id, type, source, output, file_size, status="completed"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(
            "INSERT INTO history (user_id, type, source, output, file_size, status, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, type, source, output, file_size, status, now)
        )
        self.conn.commit()
    
    def get_history(self, user_id, limit=10):
        return self.conn.execute(
            "SELECT * FROM history WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
    
    def update_stats(self, user_id, download_type, file_size=0):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(
            "UPDATE stats SET total_downloads=total_downloads+1, total_size=total_size+?, "
            "youtube_downloads=youtube_downloads+?, direct_downloads=direct_downloads+?, uploads=uploads+? "
            "WHERE user_id=?",
            (
                file_size,
                1 if download_type == "youtube" else 0,
                1 if download_type == "direct" else 0,
                1 if download_type == "upload" else 0,
                user_id
            )
        )
        self.conn.commit()
    
    def get_stats(self, user_id):
        return self.conn.execute("SELECT * FROM stats WHERE user_id=?", (user_id,)).fetchone()
    
    def get_total_stats(self):
        return self.conn.execute("""
            SELECT 
                COUNT(DISTINCT user_id) as total_users,
                SUM(total_downloads) as total_downloads,
                SUM(total_size) as total_size
            FROM stats
        """).fetchone()
    
    def get_user_settings(self, user_id):
        row = self.conn.execute("SELECT settings FROM users WHERE user_id=?", (user_id,)).fetchone()
        return json.loads(row["settings"]) if row and row["settings"] else {}
    
    def save_user_settings(self, user_id, settings):
        self.conn.execute(
            "UPDATE users SET settings=? WHERE user_id=?",
            (json.dumps(settings), user_id)
        )
        self.conn.commit()
    
    def add_download(self, user_id, url, file_name):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.conn.execute(
            "INSERT INTO downloads (user_id, url, file_name, status, start_date) VALUES (?, ?, ?, 'pending', ?)",
            (user_id, url, file_name, now)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_download_status(self, download_id, status, progress=0):
        self.conn.execute(
            "UPDATE downloads SET status=?, progress=? WHERE id=?",
            (status, progress, download_id)
        )
        self.conn.commit()
    
    def get_active_downloads_count(self, user_id):
        return self.conn.execute(
            "SELECT COUNT(*) as count FROM downloads WHERE user_id=? AND status IN ('pending', 'downloading')",
            (user_id,)
        ).fetchone()["count"]
    
    def cancel_download(self, user_id, download_id):
        self.conn.execute(
            "UPDATE downloads SET status='cancelled' WHERE id=? AND user_id=?",
            (download_id, user_id)
        )
        self.conn.commit()

db = Database()

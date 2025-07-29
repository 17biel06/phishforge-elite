import sqlite3
import os

DB_FILE = "phishforge.db"

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Campaigns table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            template_type TEXT NOT NULL,
            cloned_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        # Captured data table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS captured_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            data TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
        );
        """)
        # Admin user table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        );
        """)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"[ERROR] Error al inicializar la base de datos: {e}")

def get_db_connection():
    """Establishes a connection to the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"[ERROR] Error al conectar con la base de datos: {e}")
        return None


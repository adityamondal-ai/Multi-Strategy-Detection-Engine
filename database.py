import sqlite3
import os

APP_DIR = os.path.expanduser('~/.multi_strategy_scanner')
os.makedirs(APP_DIR, exist_ok=True)
DB_PATH = os.path.join(APP_DIR, 'history.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # We will recreate the tables if they don't exist, but since the schema changed, 
    # we should ideally handle migrations or just let it recreate since it's a new directory.
    c.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            entry_date TEXT,
            entry_price REAL,
            sl REAL,
            tp REAL,
            risk_status TEXT,
            capital_usage TEXT,
            strategy TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            entry_date TEXT,
            entry_price REAL,
            sl REAL,
            tp REAL,
            risk_status TEXT,
            capital_usage TEXT,
            strategy TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return default

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def add_entry(symbol, entry_date, entry_price, sl, tp, risk_status, capital_usage, strategy):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO entries (symbol, entry_date, entry_price, sl, tp, risk_status, capital_usage, strategy)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (symbol, entry_date, entry_price, sl, tp, risk_status, capital_usage, strategy))
    conn.commit()
    conn.close()

def get_all_entries(strategy):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM entries WHERE strategy=? ORDER BY id DESC", (strategy,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_entries(strategy):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM entries WHERE strategy=?", (strategy,))
    conn.commit()
    conn.close()

def add_to_watchlist(symbol, entry_date, entry_price, sl, tp, risk_status, capital_usage, strategy):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO watchlist (symbol, entry_date, entry_price, sl, tp, risk_status, capital_usage, strategy)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (symbol, entry_date, entry_price, sl, tp, risk_status, capital_usage, strategy))
    conn.commit()
    conn.close()

def remove_from_watchlist(item_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM watchlist WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def get_all_watchlist(strategy):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM watchlist WHERE strategy=? ORDER BY id DESC", (strategy,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

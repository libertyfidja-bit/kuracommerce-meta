"""Tiny SQLite store for merchant listings.

Render's free tier has an ephemeral disk: the file is wiped on redeploy/restart.
For a permanent demo, attach a Render Disk and point DB_PATH at it
(for example DB_PATH=/var/data/kuracommerce.db), or swap in a hosted database.
"""
import json
import os
import sqlite3
import time

DB_PATH = os.getenv("DB_PATH", "kuracommerce.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at REAL NOT NULL,
                phone TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT,
                price TEXT,
                stock INTEGER,
                location_name TEXT,
                lat REAL,
                lng REAL,
                payload TEXT
            )""")


def save_listing(phone, title, category, price, stock, location_name, lat, lng, payload) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO listings (created_at, phone, title, category, price, stock,"
            " location_name, lat, lng, payload) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (time.time(), phone, title, category, price, stock, location_name, lat, lng,
             json.dumps(payload)),
        )
        return cur.lastrowid


def list_listings(limit=200, with_payload=False):
    with _conn() as c:
        rows = c.execute("SELECT * FROM listings ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for r in rows:
        item = dict(r)
        payload = item.pop("payload")
        if with_payload:
            item["payload"] = json.loads(payload) if payload else {}
        out.append(item)
    return out


def low_stock_for(phone, threshold=2):
    with _conn() as c:
        rows = c.execute(
            "SELECT title, stock FROM listings WHERE phone = ? AND stock <= ? ORDER BY id DESC LIMIT 5",
            (phone, threshold),
        ).fetchall()
    return [dict(r) for r in rows]

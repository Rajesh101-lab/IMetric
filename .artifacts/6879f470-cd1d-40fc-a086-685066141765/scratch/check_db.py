import sqlite3
import os

db_path = "pagemetrics.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Pages table columns
    cursor.execute("PRAGMA table_info(pages)")
    pages_cols = [row[1] for row in cursor.fetchall()]
    print("Current columns in pages:", pages_cols)

    for col_name, col_type in [
        ("status", "VARCHAR(20) DEFAULT 'ready' NOT NULL"),
        ("source", "VARCHAR(20) DEFAULT 'official' NOT NULL"),
        ("fallback_reason", "VARCHAR(50)"),
        ("error_kind", "VARCHAR(50)"),
        ("error_message", "VARCHAR(255)"),
    ]:
        if col_name not in pages_cols:
            print(f"Adding '{col_name}' to pages...")
            cursor.execute(f"ALTER TABLE pages ADD COLUMN {col_name} {col_type}")

    # 2. Page Snapshots table columns
    cursor.execute("PRAGMA table_info(page_snapshots)")
    snapshots_cols = [row[1] for row in cursor.fetchall()]
    print("Current columns in page_snapshots:", snapshots_cols)

    for col_name, col_type in [
        ("source", "VARCHAR(20) DEFAULT 'official' NOT NULL"),
        ("fallback_reason", "VARCHAR(50)"),
    ]:
        if col_name not in snapshots_cols:
            print(f"Adding '{col_name}' to page_snapshots...")
            cursor.execute(f"ALTER TABLE page_snapshots ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()
    print("Database migration for pages and snapshots completed successfully!")

import sqlite3
import os

db_path = "pagemetrics.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(pages)")
    columns = [row[1] for row in cursor.fetchall()]
    print("Current columns in pages table:", columns)

    new_cols = [
        ("status", "VARCHAR(20) DEFAULT 'ready' NOT NULL"),
        ("source", "VARCHAR(20) DEFAULT 'official' NOT NULL"),
        ("fallback_reason", "VARCHAR(50)"),
        ("error_kind", "VARCHAR(50)"),
        ("error_message", "VARCHAR(255)"),
    ]

    for col_name, col_type in new_cols:
        if col_name not in columns:
            print(f"Adding missing column '{col_name}' to pages table...")
            cursor.execute(f"ALTER TABLE pages ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()
    print("Database migration completed successfully!")

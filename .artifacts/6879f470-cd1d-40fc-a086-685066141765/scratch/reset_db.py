import sqlite3
import os

db_path = "pagemetrics.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE pages SET status='ready', error_kind=NULL, error_message=NULL, last_refresh_error=NULL")
    conn.commit()
    conn.close()
    print("Database pages reset successfully.")

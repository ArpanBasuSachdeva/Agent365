import os
import psycopg2
from dotenv import load_dotenv
import time
from datetime import datetime
from typing import Optional

# Load environment variables from a .env file if present
load_dotenv()

# Database configuration with fallbacks
db_config = {
    "dbname": os.environ.get("PGDATABASE", "office_agent"),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD", "password"),
    "host": os.environ.get("PGHOST", "localhost"),
    "port": os.environ.get("PGPORT", "5432"),
}

def _get_connection():
    return psycopg2.connect(**db_config)

def ensure_office_agent_table_exists():
    create_table_query = (
        "CREATE TABLE IF NOT EXISTS OfficeAgent ("
        "id SERIAL PRIMARY KEY, "
        "UserName VARCHAR(30) NOT NULL, "
        "ChatName VARCHAR(100) NOT NULL, "
        "InputFilePath VARCHAR(500) NOT NULL, "
        "OutputFilePath VARCHAR(500) NOT NULL, "
        "Query VARCHAR(10000) NOT NULL, "
        "Remarks VARCHAR(10000) NOT NULL, "
        "CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "Status VARCHAR(20) DEFAULT 'SUCCESS'"
        ");"
    )
    conn = None
    cursor = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()
    except Exception as e:
        print("Error ensuring OfficeAgent table:", e)
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

def insert_office_agent_record(user_id: str, chat_name: str, input_file_path: str, output_file_path: str, query: str, remarks: str, status: str = "SUCCESS"):
    """Insert a new record into OfficeAgent table"""
    ensure_office_agent_table_exists()
    insert_sql = (
        "INSERT INTO OfficeAgent (UserName, ChatName, InputFilePath, OutputFilePath, Query, Remarks, Status) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    conn = None
    cursor = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(insert_sql, (user_id, chat_name, input_file_path, output_file_path, query, remarks, status))
        conn.commit()
        print(f"Database record inserted for user: {user_id}")
        return True
    except Exception as e:
        print(f"Error inserting OfficeAgent record: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

def get_user_history(user_id: str, limit: int = 10) -> list:
    """Get user's processing history"""
    ensure_office_agent_table_exists()
    select_sql = (
        "SELECT id, ChatName, InputFilePath, OutputFilePath, Query, Remarks, CreatedAt, Status "
        "FROM OfficeAgent WHERE UserName = %s ORDER BY CreatedAt DESC LIMIT %s"
    )
    conn = None
    cursor = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(select_sql, (user_id, limit))
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        history = []
        for row in results:
            download_link = None
            try:
                if row[3]:
                    from pathlib import Path as _Path
                    download_link = f"/agent365/files/{_Path(row[3]).name}/download"
            except Exception:
                download_link = None
            history.append({
                "id": row[0],
                "chat_name": row[1],
                "input_file": row[2],
                "output_file": row[3],
                "query": row[4],
                "remarks": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
                "status": row[7],
                "download_link": download_link
            })
        return history
    except Exception as e:
        print(f"Error fetching user history: {e}")
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

def get_user_record_by_id(user_id: str, record_id: int) -> Optional[dict]:
    """Fetch a single OfficeAgent record by id scoped to a specific user."""
    ensure_office_agent_table_exists()
    select_sql = (
        "SELECT id, ChatName, InputFilePath, OutputFilePath, Query, Remarks, CreatedAt, Status "
        "FROM OfficeAgent WHERE UserName = %s AND id = %s"
    )
    conn = None
    cursor = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(select_sql, (user_id, record_id))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "chat_name": row[1],
            "input_file": row[2],
            "output_file": row[3],
            "query": row[4],
            "remarks": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
            "status": row[7]
        }
    except Exception as e:
        print(f"Error fetching record by id: {e}")
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

def check_file_ownership(file_path: str, user_id: str) -> bool:
    """Check if a file belongs to a specific user by querying the database"""
    ensure_office_agent_table_exists()
    # Normalize paths for comparison (handle both forward and backward slashes)
    normalized_file_path = file_path.replace("\\", "/")
    
    # Check both original and normalized paths using OR conditions
    select_sql = (
        "SELECT COUNT(*) FROM OfficeAgent "
        "WHERE UserName = %s AND ("
        "InputFilePath = %s OR OutputFilePath = %s OR "
        "REPLACE(InputFilePath, '\\', '/') = %s OR REPLACE(OutputFilePath, '\\', '/') = %s"
        ")"
    )
    conn = None
    cursor = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        # Check both normalized and original paths
        cursor.execute(select_sql, (user_id, file_path, file_path, normalized_file_path, normalized_file_path))
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"Error checking file ownership: {e}")
        return False  # Fail secure - deny access if check fails
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

def get_user_files(user_id: str) -> list:
    """Get all file paths associated with a user from the database"""
    ensure_office_agent_table_exists()
    select_sql = (
        "SELECT DISTINCT InputFilePath, OutputFilePath "
        "FROM OfficeAgent WHERE UserName = %s"
    )
    conn = None
    cursor = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(select_sql, (user_id,))
        results = cursor.fetchall()
        
        # Collect all unique file paths
        file_paths = set()
        for row in results:
            if row[0]:  # InputFilePath
                file_paths.add(row[0])
            if row[1]:  # OutputFilePath
                file_paths.add(row[1])
        
        return list(file_paths)
    except Exception as e:
        print(f"Error fetching user files: {e}")
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

def test_database_connection() -> bool:
    """Test database connection"""
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        print("Database connection successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
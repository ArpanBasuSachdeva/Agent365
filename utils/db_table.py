import os
import psycopg2

db_config = {
    "dbname": os.getenv("PGDATABASE", "Agent365"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "Ricky@1234"),
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432")
}

def _get_connection():
    return psycopg2.connect(**db_config)

def ensure_office_agent_table_exists():
    create_table_query = (
        "CREATE TABLE IF NOT EXISTS OfficeAgent ("
        "UserName VARCHAR(30) PRIMARY KEY, "
        "ChatName VARCHAR(100) NOT NULL, "
        "InputFilePath VARCHAR(500) NOT NULL, "
        "OutputFilePath VARCHAR(500) NOT NULL, "
        "Query VARCHAR(10000) NOT NULL, "
        "Remarks VARCHAR(10000) NOT NULL"
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
        print("❌ Error ensuring OfficeAgent table:", e)
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

def insert_office_agent_record(user_id: str, chat_name: str, input_file_path: str, output_file_path: str, query: str, remarks: str):
    ensure_office_agent_table_exists()
    insert_sql = (
        "INSERT INTO OfficeAgent (UserName, ChatName, InputFilePath, OutputFilePath, Query, Remarks) "
        "VALUES (%s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (UserName) DO UPDATE SET "
        "ChatName = EXCLUDED.ChatName, "
        "InputFilePath = EXCLUDED.InputFilePath, "
        "OutputFilePath = EXCLUDED.OutputFilePath, "
        "Query = EXCLUDED.Query, "
        "Remarks = EXCLUDED.Remarks"
    )
    conn = None
    cursor = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(insert_sql, (user_id, chat_name, input_file_path, output_file_path, query, remarks))
        conn.commit()
    except Exception as e:
        print("❌ Error inserting OfficeAgent record:", e)
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

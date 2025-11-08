#!/usr/bin/env python3
"""
Update OfficeAgent table to add missing columns
"""

import psycopg2
from db_table import db_config

def update_table():
    """Add missing columns to OfficeAgent table"""
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Add Status column if it doesn't exist
        cursor.execute("ALTER TABLE OfficeAgent ADD COLUMN IF NOT EXISTS Status VARCHAR(20) DEFAULT 'SUCCESS'")
        
        # Add CreatedAt column if it doesn't exist
        cursor.execute("ALTER TABLE OfficeAgent ADD COLUMN IF NOT EXISTS CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        # Add id column if it doesn't exist (make it primary key)
        cursor.execute("ALTER TABLE OfficeAgent ADD COLUMN IF NOT EXISTS id SERIAL")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Table updated successfully!")
        return True
        
    except Exception as e:
        print(f"Error updating table: {e}")
        return False

if __name__ == "__main__":
    update_table()

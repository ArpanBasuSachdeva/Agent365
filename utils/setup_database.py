#!/usr/bin/env python3
"""
Database Setup Script for Agent365
Creates the PostgreSQL database and table if they don't exist
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Setup PostgreSQL database and table"""
    print("Setting up Agent365 Database...")
    print("=" * 50)
    
    try:
        # Import database functions
        from db_table import test_database_connection, ensure_office_agent_table_exists
        
        # Test connection
        print("1. Testing database connection...")
        if test_database_connection():
            print("   Database connection successful!")
        else:
            print("   Database connection failed!")
            print("\nPlease check your PostgreSQL configuration:")
            print(f"   - Host: {os.environ.get('PGHOST', 'localhost')}")
            print(f"   - Port: {os.environ.get('PGPORT', '5432')}")
            print(f"   - Database: {os.environ.get('PGDATABASE', 'office_agent')}")
            print(f"   - User: {os.environ.get('PGUSER', 'postgres')}")
            return False
        
        # Create table
        print("\n2. Creating OfficeAgent table...")
        ensure_office_agent_table_exists()
        print("   Table created/verified successfully!")
        
        print("\nDatabase setup completed successfully!")
        print("\nNext steps:")
        print("   1. Start the API: python main_api.py")
        print("   2. Test database logging by processing a file")
        print("   3. Check user history: GET /agent365/history")
        
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install required packages: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"Setup error: {e}")
        return False

def show_env_template():
    """Show environment variable template"""
    print("\nEnvironment Variables Template:")
    print("=" * 50)
    print("Add these to your .env file:")
    print()
    print("# PostgreSQL Database Configuration")
    print("PGDATABASE=office_agent")
    print("PGUSER=postgres")
    print("PGPASSWORD=your_password_here")
    print("PGHOST=localhost")
    print("PGPORT=5432")
    print()
    print("# Other required variables...")
    print("GEMINI_API_KEY=your_gemini_api_key")
    print("API_USERNAME=admin")
    print("API_PASSWORD=password123")

if __name__ == "__main__":
    print("Agent365 Database Setup")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--env":
        show_env_template()
    else:
        success = setup_database()
        if not success:
            print("\nNeed help? Run: python utils/setup_database.py --env")
            sys.exit(1)

#!/usr/bin/env python3
"""
User Manager Script for Agent365
Simple command-line tool to manage users
"""

import sys
import getpass
from RequestHandling.HelperClass import Agent365Helper

def main():
    """Main user management interface"""
    helper = Agent365Helper()
    
    print("Agent365 User Manager")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. List users")
        print("2. Add user")
        print("3. Remove user")
        print("4. Change password")
        print("5. Test authentication")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            list_users(helper)
        elif choice == "2":
            add_user(helper)
        elif choice == "3":
            remove_user(helper)
        elif choice == "4":
            change_password(helper)
        elif choice == "5":
            test_auth(helper)
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

def list_users(helper):
    """List all users"""
    print("\nCurrent Users:")
    print("-" * 30)
    users = helper.list_users()
    for user in users:
        print(f"Username: {user['username']}")
        print(f"Role: {user['role']}")
        print(f"Created: {user['created_at']}")
        if user['last_login']:
            print(f"Last Login: {user['last_login']}")
        else:
            print("Last Login: Never")
        print("-" * 30)

def add_user(helper):
    """Add a new user"""
    print("\nAdd New User")
    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty!")
        return
    
    password = getpass.getpass("Password: ")
    if not password:
        print("Password cannot be empty!")
        return
    
    role = input("Role (user/admin) [user]: ").strip().lower()
    if not role:
        role = "user"
    
    if role not in ["user", "admin"]:
        print("Role must be 'user' or 'admin'!")
        return
    
    if helper.add_user(username, password, role):
        print(f"User '{username}' added successfully!")
    else:
        print(f"User '{username}' already exists!")

def remove_user(helper):
    """Remove a user"""
    print("\nRemove User")
    username = input("Username to remove: ").strip()
    if not username:
        print("Username cannot be empty!")
        return
    
    if helper.remove_user(username):
        print(f"User '{username}' removed successfully!")
    else:
        print(f"User '{username}' not found!")

def change_password(helper):
    """Change user password"""
    print("\nChange Password")
    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty!")
        return
    
    old_password = getpass.getpass("Current password: ")
    new_password = getpass.getpass("New password: ")
    
    if not new_password:
        print("New password cannot be empty!")
        return
    
    if helper.change_password(username, old_password, new_password):
        print(f"Password changed successfully for '{username}'!")
    else:
        print(f"Failed to change password. Check credentials or user exists.")

def test_auth(helper):
    """Test user authentication"""
    print("\nTest Authentication")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    
    if helper.authenticate_user(username, password):
        user_info = helper.get_user_info(username)
        print(f"Authentication successful!")
        print(f"Role: {user_info['role']}")
        print(f"Created: {user_info['created_at']}")
    else:
        print("Authentication failed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

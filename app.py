"""
Streamlit Frontend for Agent365
A chat-based interface for file processing with AI
"""

import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime
from pathlib import Path
import time

# Configuration
API_BASE_URL = "http://127.0.0.1:8000/agent365"

# Page configuration
st.set_page_config(
    page_title="Agent365 - AI File Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for chat-like interface with light theme - Enhanced for readability
st.markdown("""
    <style>
    /* Main app background - Light theme */
    .stApp {
        background-color: #f5f7fa;
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e3a8a;
        text-align: center;
        padding: 1.5rem 0;
        border-bottom: 3px solid #3b82f6;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #ffffff 0%, #f0f4f8 100%);
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Chat messages - Better padding */
    .chat-message {
        padding: 1.5rem 1.75rem;
        border-radius: 12px;
        margin: 1.25rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        line-height: 1.7;
        font-size: 1rem;
    }
    
    .user-message {
        background-color: #dbeafe;
        border-left: 5px solid #2563eb;
        border: 1px solid #93c5fd;
        color: #1e40af;
    }
    
    .user-message strong {
        color: #1e3a8a;
    }
    
    .assistant-message {
        background-color: #f0fdf4;
        border-left: 5px solid #16a34a;
        border: 1px solid #86efac;
        color: #166534;
    }
    
    .assistant-message strong {
        color: #14532d;
    }
    
    .error-message {
        background-color: #fef2f2;
        border-left: 5px solid #dc2626;
        color: #991b1b;
        border: 1px solid #fca5a5;
    }
    
    .error-message strong {
        color: #7f1d1d;
    }
    
    .success-message {
        background-color: #f0fdf4;
        border-left: 5px solid #16a34a;
        color: #166534;
        border: 1px solid #86efac;
    }
    
    /* Buttons - Improved sizing and padding */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background-color: #2563eb;
        color: white !important;
        border: none;
        padding: 0.875rem 1.5rem !important;
        font-weight: 600;
        font-size: 1rem;
        min-height: 48px;
        transition: all 0.3s;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.2);
        letter-spacing: 0.3px;
    }
    
    .stButton>button:hover {
        background-color: #1d4ed8;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        transform: translateY(-2px);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* File info boxes - Better padding */
    .file-info {
        background-color: #fffbeb;
        padding: 1.25rem 1.5rem;
        border-radius: 10px;
        margin: 0.75rem 0;
        border: 2px solid #fcd34d;
        color: #78350f;
        font-size: 1rem;
        line-height: 1.6;
    }
    
    /* Input fields - Enhanced visibility with proper padding */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #1e293b !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        min-height: 44px !important;
    }
    
    .stTextArea > div > div > textarea {
        background-color: #ffffff !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #1e293b !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
        outline: none !important;
    }
    
    /* Selectbox styling - Fixed for visibility */
    .stSelectbox > div > div {
        background-color: #ffffff !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
        min-height: 44px !important;
    }
    
    .stSelectbox > div > div > div {
        background-color: #ffffff !important;
        color: #1e293b !important;
        padding: 0.5rem 0.75rem !important;
    }
    
    .stSelectbox label {
        color: #1e293b !important;
        font-weight: 500 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Dropdown menu items */
    [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #1e293b !important;
    }
    
    [data-baseweb="popover"] {
        background-color: #ffffff !important;
    }
    
    [data-baseweb="menu"] {
        background-color: #ffffff !important;
    }
    
    [data-baseweb="menu"] li {
        background-color: #ffffff !important;
        color: #1e293b !important;
        padding: 0.75rem 1rem !important;
    }
    
    [data-baseweb="menu"] li:hover {
        background-color: #f1f5f9 !important;
        color: #1e293b !important;
    }
    
    /* Sidebar styling - Better spacing */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 2px solid #e2e8f0;
        padding: 1.5rem 1rem;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #1e293b;
        line-height: 1.6;
    }
    
    [data-testid="stSidebar"] .element-container {
        margin-bottom: 1.5rem;
    }
    
    /* Headers - Better contrast */
    h1, h2, h3, h4, h5, h6 {
        color: #1e293b;
        font-weight: 600;
    }
    
    /* Text - Better readability */
    p, div, span {
        color: #334155;
    }
    
    /* Expanders - Better visibility and padding */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        color: #1e293b;
        font-weight: 600;
        padding: 1rem 1.25rem;
        font-size: 1rem;
        min-height: 48px;
        display: flex;
        align-items: center;
    }
    
    .streamlit-expanderContent {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 1.5rem;
        margin-top: 0;
    }
    
    /* Info boxes - Better padding */
    .stInfo {
        background-color: #dbeafe;
        border-left: 4px solid #2563eb;
        color: #1e40af;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .stSuccess {
        background-color: #d1fae5;
        border-left: 4px solid #10b981;
        color: #065f46;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .stWarning {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        color: #92400e;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .stError {
        background-color: #fee2e2;
        border-left: 4px solid #ef4444;
        color: #991b1b;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Tabs styling - Better spacing */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #f8fafc;
        padding: 0.75rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        color: #475569;
        font-weight: 600;
        padding: 0.875rem 1.5rem;
        min-height: 48px;
        transition: all 0.3s;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f1f5f9;
        border-color: #cbd5e1;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #2563eb;
        color: #ffffff !important;
        border-color: #2563eb;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.2);
    }
    
    /* Slider styling - Better visibility */
    .stSlider {
        padding: 1rem 0;
    }
    
    .stSlider > div > div {
        background-color: #ffffff;
    }
    
    .stSlider label {
        color: #1e293b;
        font-weight: 500;
        margin-bottom: 0.75rem;
        font-size: 1rem;
    }
    
    /* Checkbox styling - Better spacing */
    .stCheckbox {
        padding: 0.75rem 0;
    }
    
    .stCheckbox > label {
        color: #1e293b;
        font-weight: 500;
        font-size: 1rem;
        padding-left: 0.5rem;
    }
    
    .stCheckbox input[type="checkbox"] {
        width: 20px;
        height: 20px;
        margin-right: 0.5rem;
    }
    
    /* Divider */
    hr {
        border-color: #e2e8f0;
        margin: 1.5rem 0;
    }
    
    /* Code blocks */
    code {
        background-color: #f1f5f9;
        color: #dc2626;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-size: 0.9em;
    }
    
    /* JSON display */
    .stJson {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 1rem;
    }
    
    /* Login page styling */
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Small text - Better contrast */
    small {
        color: #64748b;
        font-size: 0.875rem;
    }
    
    /* Links */
    a {
        color: #2563eb;
        text-decoration: none;
    }
    
    a:hover {
        color: #1d4ed8;
        text-decoration: underline;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #2563eb;
    }
    
    /* Download button - Better sizing */
    .stDownloadButton > button {
        background-color: #10b981;
        color: white !important;
        border-radius: 10px;
        padding: 0.875rem 1.5rem !important;
        font-weight: 600;
        font-size: 1rem;
        min-height: 48px;
        box-shadow: 0 2px 6px rgba(16, 185, 129, 0.2);
        transition: all 0.3s;
    }
    
    .stDownloadButton > button:hover {
        background-color: #059669;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        transform: translateY(-2px);
    }
    
    /* Radio buttons - Better visibility and spacing */
    .stRadio > div {
        background-color: #ffffff;
        padding: 1rem 1.25rem;
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        margin-bottom: 0.5rem;
    }
    
    .stRadio label {
        color: #1e293b;
        font-weight: 500;
        font-size: 1rem;
        padding: 0.5rem 0;
    }
    
    .stRadio input[type="radio"] {
        margin-right: 0.75rem;
        width: 20px;
        height: 20px;
    }
    
    /* File uploader - Better sizing */
    .stFileUploader > div {
        background-color: #ffffff;
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 2rem 1.5rem;
        min-height: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s;
    }
    
    .stFileUploader > div:hover {
        border-color: #2563eb;
        background-color: #f8fafc;
        border-style: solid;
    }
    
    .stFileUploader label {
        font-weight: 500;
        color: #1e293b;
        margin-bottom: 0.75rem;
    }
    
    /* Metric cards */
    .stMetric {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #2563eb;
    }
    
    /* Markdown text in sidebar */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #1e293b;
    }
    
    /* Better spacing for containers */
    .element-container {
        margin-bottom: 1.5rem;
    }
    
    /* Column spacing */
    [data-testid="column"] {
        padding: 0 0.75rem;
    }
    
    /* Ensure all text is readable */
    .stMarkdown {
        color: #334155;
    }
    
    /* Table styling - Better padding */
    .stDataFrame {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        overflow: auto;
    }
    
    .stDataFrame table {
        border-collapse: separate;
        border-spacing: 0;
    }
    
    .stDataFrame th {
        background-color: #f8fafc;
        color: #1e293b;
        font-weight: 600;
        padding: 0.875rem 1rem;
    }
    
    .stDataFrame td {
        padding: 0.75rem 1rem;
        color: #334155;
    }
    
    /* Ensure proper contrast for all interactive elements */
    button, input, select, textarea {
        color: #1e293b;
    }
    
    /* Better visibility for disabled elements */
    button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        background-color: #94a3b8 !important;
    }
    
    /* Headers spacing */
    h1 {
        margin-top: 0;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    h2 {
        margin-top: 1.5rem;
        margin-bottom: 1.25rem;
    }
    
    h3 {
        margin-top: 1.25rem;
        margin-bottom: 1rem;
    }
    
    /* Divider spacing */
    hr {
        margin: 2rem 0;
        border-width: 1px;
    }
    
    /* JSON display - Better padding */
    .stJson {
        padding: 1.5rem !important;
        border-radius: 10px !important;
    }
    
    /* Spinner - Better visibility */
    .stSpinner {
        padding: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'password' not in st.session_state:
    st.session_state.password = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'selected_file' not in st.session_state:
    st.session_state.selected_file = None
if 'user_files' not in st.session_state:
    st.session_state.user_files = []


def get_auth():
    """Get HTTP Basic Auth object"""
    if st.session_state.authenticated:
        return HTTPBasicAuth(st.session_state.username, st.session_state.password)
    return None


def make_request(method, endpoint, **kwargs):
    """Make authenticated API request"""
    auth = get_auth()
    if not auth:
        return None, "Not authenticated"
    
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, auth=auth, **kwargs)
        elif method.upper() == "POST":
            response = requests.post(url, auth=auth, **kwargs)
        elif method.upper() == "DELETE":
            response = requests.delete(url, auth=auth, **kwargs)
        else:
            return None, f"Unsupported method: {method}"
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend. Make sure the API is running on port 8000."
    except Exception as e:
        return None, f"Request failed: {str(e)}"


def login():
    """Login page with tabs for Login, Create User, and Change Password"""
    st.markdown('<div class="main-header">🤖 Agent365 - AI File Assistant</div>', unsafe_allow_html=True)
    
    # Create tabs for different actions
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "➕ Create User", "🔑 Change Password"])
    
    with tab1:
        st.markdown("### Login to Your Account")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary", use_container_width=True):
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                # Test authentication
                auth = HTTPBasicAuth(username, password)
                try:
                    response = requests.get(f"{API_BASE_URL}/health", auth=auth)
                    if response.status_code == 200:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.password = password
                        st.success("✅ Login successful!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend. Make sure the API is running on port 8000.")
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
    
    with tab2:
        st.markdown("### Create New User Account")
        st.info("💡 Fill in the form below to create a new user account. You'll be able to login after creation.")
        
        new_username = st.text_input("Username", key="create_username", help="Choose a unique username")
        new_password = st.text_input("Password", type="password", key="create_password", help="Choose a secure password")
        confirm_password = st.text_input("Confirm Password", type="password", key="create_confirm_password", help="Re-enter your password")
        new_role = st.selectbox("Role", ["user", "admin"], key="create_role", help="Select user role (admin has additional privileges)")
        
        if st.button("Create User", type="primary", use_container_width=True, key="create_user_btn"):
            if not new_username or not new_password:
                st.error("Please fill in both username and password")
            elif new_password != confirm_password:
                st.error("❌ Passwords do not match. Please try again.")
            elif len(new_password) < 4:
                st.error("❌ Password must be at least 4 characters long.")
            else:
                with st.spinner("Creating user account..."):
                    # Try to create user - we need admin credentials or the API should allow public registration
                    # For now, we'll try with a default admin or handle it gracefully
                    try:
                        # First, try to get admin credentials from session or use a default
                        # Since we're on login page, we'll need to handle this differently
                        # The API requires authentication, so we'll need to check if there's a way to create users without auth
                        # For now, let's try with a basic request and see what happens
                        user_data = {
                            "username": new_username,
                            "password": new_password,
                            "role": new_role
                        }
                        
                        # Try to create user - this might require admin auth
                        # We'll use a temporary approach: try without auth first, if it fails, show a message
                        try:
                            response = requests.post(f"{API_BASE_URL}/users", data=user_data)
                            if response.status_code == 200:
                                data = response.json()
                                st.success(f"✅ {data.get('message', 'User created successfully!')}")
                                st.info("💡 You can now login with your new credentials.")
                            elif response.status_code == 401:
                                st.warning("⚠️ User creation requires admin privileges. Please contact an administrator or login as admin first.")
                            else:
                                st.error(f"❌ Error: {response.text}")
                        except requests.exceptions.ConnectionError:
                            st.error("Cannot connect to backend. Make sure the API is running on port 8000.")
                    except Exception as e:
                        st.error(f"Failed to create user: {str(e)}")
    
    with tab3:
        st.markdown("### Change Your Password")
        st.info("💡 Enter your username and current password to change your password.")
        
        change_username = st.text_input("Username", key="change_username", help="Enter your username")
        old_password = st.text_input("Current Password", type="password", key="change_old_password", help="Enter your current password")
        new_password = st.text_input("New Password", type="password", key="change_new_password", help="Enter your new password")
        confirm_new_password = st.text_input("Confirm New Password", type="password", key="change_confirm_new_password", help="Re-enter your new password")
        
        if st.button("Change Password", type="primary", use_container_width=True, key="change_password_btn"):
            if not change_username or not old_password or not new_password or not confirm_new_password:
                st.error("Please fill in all fields")
            elif new_password != confirm_new_password:
                st.error("❌ New passwords do not match. Please try again.")
            elif len(new_password) < 4:
                st.error("❌ Password must be at least 4 characters long.")
            else:
                with st.spinner("Changing password..."):
                    try:
                        auth = HTTPBasicAuth(change_username, old_password)
                        password_data = {
                            "old_password": old_password,
                            "new_password": new_password
                        }
                        
                        response = requests.put(
                            f"{API_BASE_URL}/users/{change_username}/password",
                            auth=auth,
                            data=password_data
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ {data.get('message', 'Password changed successfully!')}")
                            st.info("💡 You can now login with your new password.")
                        else:
                            st.error(f"❌ Error {response.status_code}: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to backend. Make sure the API is running on port 8000.")
                    except Exception as e:
                        st.error(f"Failed to change password: {str(e)}")


def logout():
    """Logout function"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.password = None
    st.session_state.chat_history = []
    st.session_state.selected_file = None
    st.session_state.user_files = []
    st.rerun()


def load_user_files():
    """Load user's files"""
    data, error = make_request("GET", "/user-files")
    if error:
        st.session_state.user_files = []
        return []
    files = data.get("files", [])
    st.session_state.user_files = files
    return files


def add_to_chat_history(role, message, file_info=None):
    """Add message to chat history"""
    st.session_state.chat_history.append({
        "role": role,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_info": file_info
    })


def main_app():
    """Main application interface"""
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<div class="main-header">🤖 Agent365 - AI File Assistant</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='padding: 1rem; background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0;'><strong style='color: #1e293b;'>User:</strong> <span style='color: #475569;'>{st.session_state.username}</span></div>", unsafe_allow_html=True)
        if st.button("Logout"):
            logout()
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Navigation")
        page = st.radio(
            "Select Page",
            ["💬 Chat", "📤 Upload", "📋 History", "📚 Versions", "🗂️ My Files", "⏪ Rollback"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Quick file selector
        st.subheader("📄 Quick File Select")
        files = load_user_files()
        if files:
            file_names = [f["name"] for f in files]
            selected = st.selectbox(
                "Select a file to work with",
                ["None"] + file_names,
                index=0 if not st.session_state.selected_file else 
                      (file_names.index(st.session_state.selected_file) + 1 if st.session_state.selected_file in file_names else 0)
            )
            if selected != "None":
                st.session_state.selected_file = selected
            else:
                st.session_state.selected_file = None
        else:
            st.info("No files available. Upload a file first.")
            st.session_state.selected_file = None
    
    # Main content area
    if page == "💬 Chat":
        chat_page()
    elif page == "📤 Upload":
        upload_page()
    elif page == "📋 History":
        history_page()
    elif page == "📚 Versions":
        versions_page()
    elif page == "🗂️ My Files":
        my_files_page()
    elif page == "⏪ Rollback":
        rollback_page()


def chat_page():
    """Chat interface for file processing"""
    st.header("💬 Chat with Your Files")
    
    # File selection
    files = st.session_state.user_files
    if not files:
        st.warning("No files available. Please upload a file first.")
        return
    
    file_names = [f["name"] for f in files]
    selected_file = st.selectbox(
        "Select a file to chat with",
        file_names,
        index=file_names.index(st.session_state.selected_file) if st.session_state.selected_file in file_names else 0
    )
    
    if selected_file:
        st.session_state.selected_file = selected_file
        st.info(f"📄 Working with: **{selected_file}**")
    
    st.divider()
    
    # Chat history display
    chat_container = st.container()
    with chat_container:
        if st.session_state.chat_history:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {msg["message"]}<br><small>{msg["timestamp"]}</small></div>', unsafe_allow_html=True)
                elif msg["role"] == "assistant":
                    st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {msg["message"]}<br><small>{msg["timestamp"]}</small></div>', unsafe_allow_html=True)
                elif msg["role"] == "error":
                    st.markdown(f'<div class="chat-message error-message"><strong>Error:</strong> {msg["message"]}</div>', unsafe_allow_html=True)
        else:
            st.info("👋 Start a conversation by typing a message below!")
    
    st.divider()
    
    # Chat input
    prompt = st.text_area(
        "Enter your instruction",
        placeholder="e.g., Add a new row with data, Format the document, etc.",
        height=100
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        return_file = st.checkbox("Download file", value=False)
    with col2:
        if st.button("Send Message", type="primary", use_container_width=True):
            if not selected_file:
                st.error("Please select a file first!")
            elif not prompt.strip():
                st.error("Please enter a message!")
            else:
                with st.spinner("Processing your request..."):
                    # Add user message to history
                    add_to_chat_history("user", prompt)
                    
                    # Make API call
                    files_data = {"prompt": prompt, "filename": selected_file, "return_file": return_file}
                    data, error = make_request("POST", "/chat", data=files_data)
                    
                    if error:
                        add_to_chat_history("error", error)
                        st.error(error)
                    else:
                        # Extract response message
                        message = data.get("message", "Processing completed")
                        if "summary" in data:
                            message += f"\n\n{data['summary']}"
                        
                        add_to_chat_history("assistant", message)
                        
                        # Handle file download if requested
                        if return_file and "download_link" in data:
                            st.success("✅ Processing completed!")
                            # Create download button with authenticated request
                            download_url = f"{API_BASE_URL}{data['download_link']}"
                            auth = get_auth()
                            try:
                                response = requests.get(download_url, auth=auth, stream=True)
                                if response.status_code == 200:
                                    st.download_button(
                                        label="📥 Download Processed File",
                                        data=response.content,
                                        file_name=data.get('output_file_name', 'processed_file'),
                                        mime=response.headers.get('content-type', 'application/octet-stream')
                                    )
                            except Exception as e:
                                st.warning(f"Download link: {download_url}")
                        else:
                            st.success("✅ Processing completed!")
                        
                        st.rerun()


def upload_page():
    """File upload page"""
    st.header("📤 Upload File")
    
    uploaded_file = st.file_uploader(
        "Choose a file to upload",
        type=["docx", "xlsx", "pptx"],
        help="Supported formats: .docx, .xlsx, .pptx"
    )
    
    if uploaded_file:
        st.info(f"📄 Selected: **{uploaded_file.name}** ({uploaded_file.size} bytes)")
        
        if st.button("Upload File", type="primary"):
            with st.spinner("Uploading file..."):
                auth = get_auth()
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(
                        f"{API_BASE_URL}/upload",
                        auth=auth,
                        files=files
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ File uploaded successfully!")
                        st.json(data)
                        
                        # Update file list
                        load_user_files()
                        st.session_state.selected_file = data.get("filename")
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {response.text}")
                except Exception as e:
                    st.error(f"Upload error: {str(e)}")


def history_page():
    """Processing history page"""
    st.header("📋 Processing History")
    
    limit = st.slider("Number of records", 5, 50, 10, 5)
    
    if st.button("Refresh History", type="primary"):
        with st.spinner("Loading history..."):
            data, error = make_request("GET", f"/history?limit={limit}")
            
            if error:
                st.error(error)
            else:
                history = data.get("history", [])
                
                if history:
                    st.success(f"Found {len(history)} records")
                    
                    for record in history:
                        with st.expander(f"📄 {record.get('chat_name', 'Unknown')} - {record.get('timestamp', 'N/A')}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Status:** {record.get('status', 'N/A')}")
                                st.write(f"**Input File:** {Path(record.get('input_file', 'N/A')).name}")
                            with col2:
                                st.write(f"**Output File:** {Path(record.get('output_file', 'N/A')).name}")
                                if record.get('download_link'):
                                    download_url = f"{API_BASE_URL}{record['download_link']}"
                                    auth = get_auth()
                                    try:
                                        response = requests.get(download_url, auth=auth, stream=True)
                                        if response.status_code == 200:
                                            file_name = Path(record.get('output_file', 'file')).name
                                            st.download_button(
                                                label="📥 Download",
                                                data=response.content,
                                                file_name=file_name,
                                                mime=response.headers.get('content-type', 'application/octet-stream'),
                                                key=f"dl_history_{record.get('id')}"
                                            )
                                    except Exception:
                                        st.markdown(f"**Download:** [Link]({download_url})")
                            
                            st.write(f"**Query:** {record.get('query', 'N/A')}")
                            if record.get('remarks'):
                                st.write(f"**Remarks:** {record.get('remarks')}")
                else:
                    st.info("No history records found.")
    else:
        st.info("Click 'Refresh History' to load your processing history.")


def versions_page():
    """File versions page"""
    st.header("📚 File Versions")
    
    files = st.session_state.user_files
    file_names = ["All Files"] + [f["name"] for f in files] if files else ["All Files"]
    
    selected_filter = st.selectbox("Filter by filename (optional)", file_names)
    
    limit = st.slider("Number of versions", 5, 50, 25, 5)
    
    if st.button("Load Versions", type="primary"):
        with st.spinner("Loading versions..."):
            endpoint = f"/versions?limit={limit}"
            if selected_filter != "All Files":
                endpoint += f"&filename={selected_filter}"
            
            data, error = make_request("GET", endpoint)
            
            if error:
                st.error(error)
            else:
                versions = data.get("versions", [])
                
                if versions:
                    st.success(f"Found {len(versions)} version(s)")
                    
                    for version in versions:
                        with st.expander(f"📄 Version ID: {version.get('id')} - {version.get('timestamp', 'N/A')}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Status:** {version.get('status', 'N/A')}")
                                st.write(f"**Input:** {Path(version.get('input_file', 'N/A')).name}")
                            with col2:
                                st.write(f"**Output:** {Path(version.get('output_file', 'N/A')).name}")
                                if version.get('download_link'):
                                    download_url = f"{API_BASE_URL}{version['download_link']}"
                                    auth = get_auth()
                                    try:
                                        response = requests.get(download_url, auth=auth, stream=True)
                                        if response.status_code == 200:
                                            file_name = Path(version.get('output_file', 'file')).name
                                            st.download_button(
                                                label="📥 Download",
                                                data=response.content,
                                                file_name=file_name,
                                                mime=response.headers.get('content-type', 'application/octet-stream'),
                                                key=f"dl_version_{version.get('id')}"
                                            )
                                    except Exception:
                                        st.markdown(f"**Download:** [Link]({download_url})")
                            
                            st.write(f"**Query:** {version.get('query', 'N/A')}")
                            if version.get('remarks'):
                                st.write(f"**Remarks:** {version.get('remarks')}")
                else:
                    st.info("No versions found.")


def my_files_page():
    """User files page"""
    st.header("🗂️ My Files")
    
    if st.button("Refresh Files", type="primary"):
        with st.spinner("Loading files..."):
            files = load_user_files()
            
            if files:
                st.success(f"Found {len(files)} file(s)")
                
                for file_info in files:
                    with st.expander(f"📄 {file_info['name']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Size:** {file_info['size']:,} bytes")
                            st.write(f"**Path:** {file_info['path']}")
                        with col2:
                            modified = datetime.fromtimestamp(file_info['modified']).strftime("%Y-%m-%d %H:%M:%S")
                            st.write(f"**Modified:** {modified}")
                            if file_info.get('download_link'):
                                download_url = f"{API_BASE_URL}{file_info['download_link']}"
                                auth = get_auth()
                                try:
                                    response = requests.get(download_url, auth=auth, stream=True)
                                    if response.status_code == 200:
                                        st.download_button(
                                            label="📥 Download",
                                            data=response.content,
                                            file_name=file_info['name'],
                                            mime=response.headers.get('content-type', 'application/octet-stream'),
                                            key=f"dl_file_{file_info['name']}"
                                        )
                                except Exception:
                                    st.markdown(f"**Download:** [Link]({download_url})")
                        
                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button(f"Select for Chat", key=f"select_{file_info['name']}"):
                                st.session_state.selected_file = file_info['name']
                                st.success(f"Selected: {file_info['name']}")
                                st.rerun()
                        with col2:
                            if st.button(f"Delete", key=f"delete_{file_info['name']}"):
                                data, error = make_request("DELETE", f"/files/{file_info['name']}")
                                if error:
                                    st.error(error)
                                else:
                                    st.success("File deleted!")
                                    load_user_files()
                                    st.rerun()
            else:
                st.info("No files found. Upload a file to get started!")
    else:
        st.info("Click 'Refresh Files' to load your files.")


def rollback_page():
    """Rollback page"""
    st.header("⏪ Rollback to Previous Version")
    
    files = st.session_state.user_files
    if not files:
        st.warning("No files available. Please upload a file first.")
        return
    
    file_names = [f["name"] for f in files]
    selected_file = st.selectbox("Select file to rollback", file_names)
    
    if selected_file:
        # Load versions for this file
        with st.spinner("Loading versions..."):
            data, error = make_request("GET", f"/versions?limit=50&filename={selected_file}")
            
            if error:
                st.error(error)
            else:
                versions = data.get("versions", [])
                
                if versions:
                    st.info(f"Found {len(versions)} version(s) for {selected_file}")
                    
                    # Create version selector
                    version_options = []
                    for v in versions:
                        timestamp = v.get('timestamp', 'N/A')
                        status = v.get('status', 'N/A')
                        version_options.append(f"ID: {v.get('id')} - {timestamp} ({status})")
                    
                    selected_version = st.selectbox("Select version to rollback to", version_options)
                    
                    if selected_version:
                        # Extract record ID
                        record_id = int(selected_version.split("ID: ")[1].split(" -")[0])
                        
                        st.warning(f"⚠️ This will replace **{selected_file}** with version ID **{record_id}**")
                        
                        if st.button("Rollback", type="primary"):
                            with st.spinner("Rolling back..."):
                                rollback_data = {"filename": selected_file, "record_id": record_id}
                                data, error = make_request("POST", "/rollback", data=rollback_data)
                                
                                if error:
                                    st.error(error)
                                else:
                                    st.success("✅ Rollback successful!")
                                    st.json(data)
                                    load_user_files()
                else:
                    st.info("No versions found for this file.")


# Main app logic
if not st.session_state.authenticated:
    login()
else:
    main_app()


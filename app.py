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
    /* Main app background - Soft lavender tint */
    .stApp {
        background-color: #f8f7fc;
    }

    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Header styling - Soft lavender gradient */
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #2c3e50;
        text-align: center;
        padding: 2rem 1.5rem;
        border-bottom: 2px solid #e8eaf6;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #fdfbff 0%, #f3f2f8 100%);
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(121, 134, 203, 0.08);
    }

    /* Chat messages - Centered text with soothing colors */
    .chat-message {
        padding: 1.75rem 2rem;
        border-radius: 14px;
        margin: 1.5rem 0;
        box-shadow: 0 1px 4px rgba(121, 134, 203, 0.1);
        background-color: #ffffff;
        border: 1px solid #e8eaf6;
        line-height: 1.8;
        font-size: 1rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
        text-align: left;
    }

    .user-message {
        background-color: #f3f2f8;
        border-left: 4px solid #9fa8da;
        border: 1px solid #c5cae9;
        color: #2c3e50;
    }

    .user-message strong {
        color: #1a3a5c;
    }

    .assistant-message {
        background-color: #f1f8f4;
        border-left: 4px solid #81c784;
        border: 1px solid #c8e6c9;
        color: #2c3e50;
    }

    .assistant-message strong {
        color: #2d5a2d;
    }

    .error-message {
        background-color: #fff4f1;
        border-left: 4px solid #ffab91;
        color: #662c2c;
        border: 1px solid #ffccbc;
    }

    .error-message strong {
        color: #551f1f;
    }

    .success-message {
        background-color: #f1f8f4;
        border-left: 4px solid #81c784;
        color: #2d5a2d;
        border: 1px solid #c8e6c9;
    }

    /* Buttons - Centered text with soft lavender */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        background-color: #9fa8da !important;
        color: white !important;
        border: none;
        padding: 1rem 2rem !important;
        font-weight: 500;
        font-size: 1rem;
        min-height: 52px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(159, 168, 218, 0.2);
        letter-spacing: 0.2px;
        white-space: normal;
        line-height: 1.5;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }

    .stButton>button:hover {
        background-color: #7986cb !important;
        box-shadow: 0 3px 8px rgba(121, 134, 203, 0.25);
        transform: translateY(-1px);
    }

    .stButton>button:active {
        transform: translateY(0);
    }

    /* File info boxes - Soft peach background */
    .file-info {
        background-color: #fff8f0;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid #ffe0b2;
        color: #5c4a2c;
        font-size: 1rem;
        line-height: 1.7;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }

    /* Input fields - White with lavender borders */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        border: 1px solid #c5cae9 !important;
        border-radius: 10px !important;
        color: #2c3e50 !important;
        padding: 0.875rem 1.25rem !important;
        font-size: 1rem !important;
        min-height: 50px !important;
        line-height: 1.5 !important;
        text-align: left !important;
    }

    .stTextArea > div > div > textarea {
        background-color: #ffffff !important;
        border: 1px solid #c5cae9 !important;
        border-radius: 10px !important;
        color: #2c3e50 !important;
        padding: 1rem 1.25rem !important;
        font-size: 1rem !important;
        line-height: 1.7 !important;
        min-height: 120px !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #9fa8da !important;
        box-shadow: 0 0 0 3px rgba(159, 168, 218, 0.1) !important;
        outline: none !important;
    }

    /* Selectbox styling - White with lavender accents - FIX DARK DROPDOWN */
    .stSelectbox > div > div {
        background-color: #ffffff !important;
        border: 1px solid #c5cae9 !important;
        border-radius: 10px !important;
        padding: 0.75rem 1rem !important;
        min-height: 50px !important;
        display: flex !important;
        align-items: center !important;
    }

    .stSelectbox > div > div > div {
        background-color: #ffffff !important;
        color: #2c3e50 !important;
        padding: 0.5rem 0.75rem !important;
        font-size: 1rem !important;
        line-height: 1.5 !important;
    }

    .stSelectbox label {
        color: #2c3e50 !important;
        font-weight: 500 !important;
        margin-bottom: 0.75rem !important;
        font-size: 1rem !important;
    }

    /* Fix dropdown dark background - Multiple selectors */
    [data-baseweb="select"] {
        background-color: #ffffff !important;
    }

    [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #2c3e50 !important;
    }

    [data-baseweb="select"] input {
        background-color: #ffffff !important;
        color: #2c3e50 !important;
    }

    /* Dropdown popover - Light lavender */
    [data-baseweb="popover"] {
        background-color: #fdfbff !important;
        border: 1px solid #e8eaf6 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 12px rgba(121, 134, 203, 0.12) !important;
    }

    /* Dropdown menu container - Light lavender */
    [data-baseweb="menu"] {
        background-color: #fdfbff !important;
        padding: 0.5rem !important;
    }

    /* Dropdown menu items - Light lavender */
    [data-baseweb="menu"] li {
        background-color: #fdfbff !important;
        color: #2c3e50 !important;
        padding: 0.875rem 1.25rem !important;
        border-radius: 8px !important;
        margin: 0.25rem 0 !important;
        font-size: 1rem !important;
        line-height: 1.5 !important;
        text-align: left !important;
    }

    [data-baseweb="menu"] li:hover {
        background-color: #e8eaf6 !important;
        color: #2c3e50 !important;
    }

    /* Override dark dropdown options */
    [role="option"] {
        background-color: #fdfbff !important;
        color: #2c3e50 !important;
    }

    [role="option"]:hover {
        background-color: #e8eaf6 !important;
        color: #2c3e50 !important;
    }

    /* Sidebar styling - Soft lavender tint */
    [data-testid="stSidebar"] {
        background-color: #fdfbff;
        border-right: 1px solid #e8eaf6;
        padding: 2rem 1.25rem;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: #2c3e50;
        line-height: 1.7;
    }

    [data-testid="stSidebar"] .element-container {
        margin-bottom: 1.75rem;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50;
        font-weight: 600;
        line-height: 1.4;
    }

    /* Text */
    p, div, span, label {
        color: #4a5568;
        line-height: 1.7;
    }

    /* Expanders - Soft lavender background */
    .streamlit-expanderHeader {
        background-color: #f3f2f8;
        border: 1px solid #e8eaf6;
        border-radius: 10px;
        color: #2c3e50;
        font-weight: 500;
        padding: 1.25rem 1.5rem;
        font-size: 1rem;
        min-height: 54px;
        display: flex;
        align-items: center;
        line-height: 1.5;
    }

    .streamlit-expanderContent {
        background-color: #fdfbff;
        border: 1px solid #e8eaf6;
        border-top: none;
        border-radius: 0 0 10px 10px;
        padding: 1.75rem 1.5rem;
        margin-top: 0;
    }

    /* Info boxes */
    .stInfo {
        background-color: #f3f2f8;
        border-left: 3px solid #9fa8da;
        color: #2c3e50;
        padding: 1.25rem 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        line-height: 1.7;
    }

    .stSuccess {
        background-color: #f1f8f4;
        border-left: 3px solid #81c784;
        color: #2d5a2d;
        padding: 1.25rem 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        line-height: 1.7;
    }

    .stWarning {
        background-color: #fff8f0;
        border-left: 3px solid #ffb74d;
        color: #5c4a2c;
        padding: 1.25rem 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        line-height: 1.7;
    }

    .stError {
        background-color: #fff4f1;
        border-left: 3px solid #ffab91;
        color: #662c2c;
        padding: 1.25rem 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        line-height: 1.7;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f3f2f8;
        padding: 0.875rem;
        border-radius: 12px;
        margin-bottom: 1.75rem;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border: 1px solid #e8eaf6;
        border-radius: 10px;
        color: #4a5568;
        font-weight: 500;
        padding: 1rem 1.75rem;
        min-height: 50px;
        transition: all 0.2s;
        white-space: normal;
        line-height: 1.5;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f3f2f8;
        border-color: #c5cae9;
    }

    .stTabs [aria-selected="true"] {
        background-color: #9fa8da;
        color: #ffffff !important;
        border-color: #9fa8da;
        box-shadow: 0 2px 4px rgba(159, 168, 218, 0.2);
    }

    /* Slider */
    .stSlider {
        padding: 1.25rem 0;
    }

    .stSlider > div > div {
        background-color: #fdfbff;
    }

    .stSlider label {
        color: #2c3e50;
        font-weight: 500;
        margin-bottom: 1rem;
        font-size: 1rem;
    }

    /* Checkbox */
    .stCheckbox {
        padding: 1rem 0;
        display: flex;
        align-items: center;
    }

    .stCheckbox > label {
        color: #2c3e50;
        font-weight: 500;
        font-size: 1rem;
        padding-left: 0.625rem;
        line-height: 1.6;
        display: flex;
        align-items: center;
    }

    .stCheckbox input[type="checkbox"] {
        width: 22px;
        height: 22px;
        margin-right: 0.75rem;
        accent-color: #9fa8da;
    }

    /* Divider */
    hr {
        border-color: #e8eaf6;
        margin: 2rem 0;
    }

    /* Code blocks */
    code {
        background-color: #fff8f0;
        color: #d97070;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        font-size: 0.9em;
        word-wrap: break-word;
    }

    /* JSON display */
    .stJson {
        background-color: #f3f2f8;
        border: 1px solid #e8eaf6;
        border-radius: 10px;
        padding: 1.5rem;
    }

    /* Login container */
    .login-container {
        max-width: 520px;
        margin: 0 auto;
        padding: 2.5rem;
        background-color: #ffffff;
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(159, 168, 218, 0.12);
    }

    /* Small text */
    small {
        color: #718096 !important;
        font-size: 0.875rem;
        line-height: 1.6;
    }

    /* Links */
    a {
        color: #7986cb;
        text-decoration: none;
        transition: color 0.2s;
    }

    a:hover {
        color: #5c6bc0;
        text-decoration: underline;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #9fa8da;
    }

    /* Download button */
    .stDownloadButton > button {
        background-color: #81c784 !important;
        color: white !important;
        border-radius: 12px;
        padding: 1rem 2rem !important;
        font-weight: 500;
        font-size: 1rem;
        min-height: 52px;
        box-shadow: 0 2px 4px rgba(129, 199, 132, 0.2);
        transition: all 0.2s;
        white-space: normal;
        line-height: 1.5;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }

    .stDownloadButton > button:hover {
        background-color: #66bb6a !important;
        box-shadow: 0 3px 8px rgba(129, 199, 132, 0.25);
        transform: translateY(-1px);
    }

    /* Radio buttons */
    .stRadio > div {
        background-color: #fdfbff;
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        border: 1px solid #e8eaf6;
        margin-bottom: 0.75rem;
    }

    .stRadio label {
        color: #2c3e50;
        font-weight: 500;
        font-size: 1rem;
        padding: 0.625rem 0;
        line-height: 1.6;
        display: flex;
        align-items: center;
    }

    .stRadio input[type="radio"] {
        margin-right: 1rem;
        width: 20px;
        height: 20px;
        accent-color: #9fa8da;
    }

    /* File uploader - FIX DARK BACKGROUND */
    .stFileUploader {
        background-color: transparent !important;
    }

    .stFileUploader > div {
        background-color: #ffffff !important;
        border: 2px dashed #c5cae9 !important;
        border-radius: 14px !important;
        padding: 2.5rem 2rem !important;
        min-height: 140px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s !important;
    }

    .stFileUploader > div:hover {
        border-color: #9fa8da !important;
        background-color: #f3f2f8 !important;
        border-style: solid !important;
    }

    .stFileUploader label {
        font-weight: 500 !important;
        color: #2c3e50 !important;
        margin-bottom: 1rem !important;
        font-size: 1rem !important;
    }

    .stFileUploader section {
        background-color: #ffffff !important;
        border: 2px dashed #c5cae9 !important;
        border-radius: 14px !important;
        padding: 2.5rem 2rem !important;
    }

    .stFileUploader section:hover {
        border-color: #9fa8da !important;
        background-color: #f3f2f8 !important;
        border-style: solid !important;
    }

    .stFileUploader section > div {
        background-color: transparent !important;
    }

    .stFileUploader button {
        background-color: #9fa8da !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        border: none !important;
    }

    .stFileUploader button:hover {
        background-color: #7986cb !important;
    }

    /* Override file uploader dark backgrounds */
    [data-testid="stFileUploader"] {
        background-color: transparent !important;
    }

    [data-testid="stFileUploader"] > div {
        background-color: #ffffff !important;
    }

    [data-testid="stFileUploader"] section {
        background-color: #ffffff !important;
        border: 2px dashed #c5cae9 !important;
        color: #2c3e50 !important;
    }

    [data-testid="stFileUploader"] section small {
        color: #718096 !important;
    }

    [data-testid="stFileUploader"] button {
        background-color: #9fa8da !important;
        color: white !important;
    }

    /* Metric cards */
    .stMetric {
        background-color: #ffffff;
        border: 1px solid #e8eaf6;
        border-radius: 12px;
        padding: 1.5rem;
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #9fa8da;
    }

    .stProgress > div > div {
        background-color: #e8eaf6;
    }

    /* Sidebar headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #2c3e50;
    }

    /* Element spacing */
    .element-container {
        margin-bottom: 1.75rem;
    }

    /* Column spacing */
    [data-testid="column"] {
        padding: 0 1rem;
    }

    /* Markdown text */
    .stMarkdown {
        color: #4a5568;
    }

    /* Table styling */
    .stDataFrame {
        background-color: #ffffff;
        border: 1px solid #e8eaf6;
        border-radius: 12px;
        padding: 1.25rem;
        overflow: auto;
    }

    .stDataFrame table {
        border-collapse: separate;
        border-spacing: 0;
    }

    .stDataFrame th {
        background-color: #f3f2f8;
        color: #2c3e50;
        font-weight: 600;
        padding: 1rem 1.25rem;
        text-align: center;
    }

    .stDataFrame td {
        padding: 0.875rem 1.25rem;
        color: #4a5568;
        text-align: center;
    }

    /* Interactive elements */
    button, input, select, textarea {
        color: #2c3e50 !important;
    }

    /* Disabled elements */
    button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        background-color: #c5cae9 !important;
    }

    /* Headers spacing */
    h1 {
        margin-top: 0;
        margin-bottom: 1.75rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e8eaf6;
    }

    h2 {
        margin-top: 1.75rem;
        margin-bottom: 1.5rem;
    }

    h3 {
        margin-top: 1.5rem;
        margin-bottom: 1.25rem;
    }

    /* Divider spacing */
    hr {
        margin: 2.5rem 0;
        border-width: 1px;
    }

    /* JSON display */
    .stJson {
        padding: 1.75rem !important;
        border-radius: 12px !important;
    }

    /* Spinner visibility */
    .stSpinner {
        padding: 2.5rem;
    }

    /* Fix emoji rendering */
    * {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji" !important;
    }

    /* Ensure text doesn't overflow */
    button, .stButton > button, .stDownloadButton > button {
        overflow: hidden;
        text-overflow: ellipsis;
        word-wrap: break-word;
        white-space: normal !important;
    }

    /* Better line height */
    p, span, div, label, button {
        line-height: 1.7;
    }

    /* Ensure selectbox text fits */
    [data-baseweb="select"] {
        min-height: 50px !important;
        background-color: #ffffff !important;
    }

    [data-baseweb="select"] > div {
        padding: 0.75rem 1rem !important;
        line-height: 1.5 !important;
        display: flex !important;
        align-items: center !important;
        background-color: #ffffff !important;
        color: #2c3e50 !important;
    }

    /* Number input */
    .stNumberInput > div > div > input {
        background-color: #ffffff !important;
        border: 1px solid #c5cae9 !important;
        border-radius: 10px !important;
        color: #2c3e50 !important;
        padding: 0.875rem 1.25rem !important;
        min-height: 50px !important;
    }

    .stNumberInput > div > div > input:focus {
        border-color: #9fa8da !important;
        box-shadow: 0 0 0 3px rgba(159, 168, 218, 0.1) !important;
    }

    /* Date input */
    .stDateInput > div > div > input {
        background-color: #ffffff !important;
        border: 1px solid #c5cae9 !important;
        border-radius: 10px !important;
        color: #2c3e50 !important;
        padding: 0.875rem 1.25rem !important;
        min-height: 50px !important;
    }

    /* Time input */
    .stTimeInput > div > div > input {
        background-color: #ffffff !important;
        border: 1px solid #c5cae9 !important;
        border-radius: 10px !important;
        color: #2c3e50 !important;
        padding: 0.875rem 1.25rem !important;
        min-height: 50px !important;
    }

    /* Multiselect */
    .stMultiSelect > div > div {
        background-color: #ffffff !important;
        border: 1px solid #c5cae9 !important;
        border-radius: 10px !important;
        min-height: 50px !important;
    }

    .stMultiSelect span[data-baseweb="tag"] {
        background-color: #e8eaf6 !important;
        color: #2c3e50 !important;
        border-radius: 6px !important;
        padding: 0.25rem 0.5rem !important;
    }

    /* Alert boxes */
    [data-testid="stAlert"] {
        background-color: #f3f2f8;
        border: 1px solid #e8eaf6;
        border-left: 3px solid #9fa8da;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
    }

    /* Success indicator */
    [data-testid="stSuccess"] {
        background-color: #f1f8f4 !important;
        border-left: 3px solid #81c784 !important;
    }

    /* Warning indicator */
    [data-testid="stWarning"] {
        background-color: #fff8f0 !important;
        border-left: 3px solid #ffb74d !important;
    }

    /* Error indicator */
    [data-testid="stError"] {
        background-color: #fff4f1 !important;
        border-left: 3px solid #ffab91 !important;
    }

    /* Info indicator */
    [data-testid="stInfo"] {
        background-color: #f3f2f8 !important;
        border-left: 3px solid #9fa8da !important;
    }

    /* Form submit button */
    .stForm button[type="submit"] {
        background-color: #9fa8da !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #f3f2f8;
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb {
        background: #c5cae9;
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #9fa8da;
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
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = None
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
    """Login page - only login functionality"""
    st.markdown('<div class="main-header">🤖 Agent365 - AI File Assistant</div>', unsafe_allow_html=True)
    
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
                    # Load user profile to get role
                    profile_response = requests.get(f"{API_BASE_URL}/profile", auth=auth)
                    if profile_response.status_code == 200:
                        profile = profile_response.json()
                        st.session_state.user_profile = profile
                        st.session_state.user_role = profile.get("role", "user")
                    else:
                        st.session_state.user_role = "user"  # Default to user if profile fails
                        st.session_state.user_profile = None
                    
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


def logout():
    """Logout function"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.password = None
    st.session_state.user_role = None
    st.session_state.user_profile = None
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
        role_badge = ""
        if st.session_state.user_role == "admin":
            role_badge = " <span style='background-color: #fef3c7; color: #92400e; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>ADMIN</span>"
        st.markdown(f"<div style='padding: 1rem; background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0;'><strong style='color: #1e293b;'>User:</strong> <span style='color: #475569;'>{st.session_state.username}</span>{role_badge}</div>", unsafe_allow_html=True)
        if st.button("Logout"):
            logout()
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Navigation")
        
        # Build navigation options based on user role
        nav_options = ["💬 Chat", "📤 Upload", "📋 History", "📚 Versions", "🗂️ My Files", "⏪ Rollback"]
        
        # Add admin-only options
        if st.session_state.user_role == "admin":
            nav_options.extend(["👥 Create User", "🔑 Change Password"])
        
        page = st.radio(
            "Select Page",
            nav_options,
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
    elif page == "👥 Create User":
        create_user_page()
    elif page == "🔑 Change Password":
        change_password_page()


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


def create_user_page():
    """Create user page - admin only"""
    if st.session_state.user_role != "admin":
        st.error("❌ Access denied. Admin privileges required.")
        return
    
    st.header("👥 Create New User Account")
    st.info("💡 Fill in the form below to create a new user account.")
    
    new_username = st.text_input("Username", key="create_username", help="Choose a unique username")
    new_password = st.text_input("Password", type="password", key="create_password", help="Choose a secure password (minimum 4 characters)")
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
                try:
                    user_data = {
                        "username": new_username,
                        "password": new_password,
                        "role": new_role
                    }
                    
                    data, error = make_request("POST", "/users", data=user_data)
                    if error:
                        st.error(f"❌ Error: {error}")
                    else:
                        st.success(f"✅ {data.get('message', 'User created successfully!')}")
                        st.info("💡 The user can now login with their credentials.")
                except Exception as e:
                    st.error(f"Failed to create user: {str(e)}")


def change_password_page():
    """Change password page - admin only"""
    if st.session_state.user_role != "admin":
        st.error("❌ Access denied. Admin privileges required.")
        return
    
    st.header("🔑 Change User Password")
    st.info("💡 Enter the username and new password to change a user's password.")
    
    change_username = st.text_input("Username", key="change_username", help="Enter the username whose password you want to change")
    new_password = st.text_input("New Password", type="password", key="change_new_password", help="Enter the new password")
    confirm_new_password = st.text_input("Confirm New Password", type="password", key="change_confirm_new_password", help="Re-enter the new password")
    
    if st.button("Change Password", type="primary", use_container_width=True, key="change_password_btn"):
        if not change_username or not new_password or not confirm_new_password:
            st.error("Please fill in all fields")
        elif new_password != confirm_new_password:
            st.error("❌ New passwords do not match. Please try again.")
        elif len(new_password) < 4:
            st.error("❌ Password must be at least 4 characters long.")
        else:
            with st.spinner("Changing password..."):
                try:
                    # For admin changing another user's password, we need to use a different approach
                    # Since the API requires old_password, we'll need to check if there's an admin override
                    # For now, we'll use the current admin's credentials to authenticate
                    auth = get_auth()
                    if not auth:
                        st.error("Not authenticated")
                        return
                    
                    # Try to change password - note: API might require old_password
                    # We'll need to handle this based on API design
                    password_data = {
                        "old_password": st.session_state.password,  # Admin's current password for auth
                        "new_password": new_password
                    }
                    
                    # Use PUT request with admin auth
                    response = requests.put(
                        f"{API_BASE_URL}/users/{change_username}/password",
                        auth=auth,
                        data=password_data
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ {data.get('message', 'Password changed successfully!')}")
                    else:
                        error_msg = response.text
                        try:
                            error_json = response.json()
                            error_msg = error_json.get('detail', error_msg)
                        except:
                            pass
                        st.error(f"❌ Error: {error_msg}")
                        st.info("💡 Note: The API may require the user's current password. If this is the case, users should change their own passwords after login.")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend. Make sure the API is running on port 8000.")
                except Exception as e:
                    st.error(f"Failed to change password: {str(e)}")


# Main app logic
if not st.session_state.authenticated:
    login()
else:
    main_app()
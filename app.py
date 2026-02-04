"""
Outbound Engine MVP
A lightweight web app for generating Cursor-specific outbound hypotheses and sequences.
"""

import streamlit as st
import os
import io
import re
import pandas as pd
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Optional Gemini import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# Load environment variables (.env first, then local_secrets.env for saved API keys)
load_dotenv()
_secrets_path = Path(__file__).parent / "local_secrets.env"
if _secrets_path.exists():
    load_dotenv(_secrets_path)


def _get_openai_key() -> str:
    try:
        s = getattr(st, "secrets", None)
        if s and "OPENAI_API_KEY" in s:
            return (s.get("OPENAI_API_KEY") or "").strip()
    except Exception:
        pass
    return (os.getenv("OPENAI_API_KEY") or st.session_state.get("openai_api_key") or "") or ""


def _get_gemini_key() -> str:
    try:
        s = getattr(st, "secrets", None)
        if s:
            # Top-level (Streamlit Cloud often uses this)
            key = s.get("GEMINI_API_KEY") if hasattr(s, "get") else getattr(s, "GEMINI_API_KEY", None)
            if key and isinstance(key, str):
                return key.strip()
            # Nested (e.g. [api_keys] section in TOML)
            if hasattr(s, "get"):
                for section in ("api_keys", "secrets", "default"):
                    sub = s.get(section) if isinstance(s.get(section), dict) else None
                    if sub and sub.get("GEMINI_API_KEY"):
                        return str(sub["GEMINI_API_KEY"]).strip()
    except Exception:
        pass
    return (os.getenv("GEMINI_API_KEY") or st.session_state.get("gemini_api_key") or "") or ""


def _inject_streamlit_secrets_into_env():
    """Copy Streamlit Cloud secrets into os.environ so all code sees them. Run once at startup."""
    try:
        s = getattr(st, "secrets", None)
        if not s:
            return
        for name in ("GEMINI_API_KEY", "OPENAI_API_KEY"):
            if os.environ.get(name):
                continue
            val = None
            # Try exact name
            if hasattr(s, "get") and name in s:
                val = s.get(name)
            if not val:
                val = getattr(s, name, None)
            # Try lowercase (some hosts normalize keys)
            if not val and hasattr(s, "get"):
                val = s.get(name.lower(), None) or s.get(name.replace("_", ""), None)
            if not val and hasattr(s, "get"):
                for section in ("api_keys", "secrets", "default"):
                    sub = s.get(section) if isinstance(s.get(section), dict) else None
                    if sub and sub.get(name):
                        val = sub[name]
                        break
            if val and isinstance(val, str) and val.strip():
                os.environ[name] = val.strip()
    except Exception:
        pass


# Configure page
st.set_page_config(
    page_title="Outbound Engine",
    page_icon="🎯",
    layout="wide"
)
_inject_streamlit_secrets_into_env()

# Inject warm color scheme CSS
def inject_warm_styles():
    """Inject warm, dynamic CSS styling for a more inviting UI."""
    st.markdown("""
    <style>
    /* Dark theme color scheme */
    :root {
        --dark-bg: #1A1A1A;
        --dark-bg-secondary: #242424;
        --dark-bg-tertiary: #2D2D2D;
        --dark-primary: #5B9BD5;
        --dark-primary-dark: #4A8BC2;
        --dark-accent: #FF6B6B;
        --dark-accent-warm: #FF8C69;
        --dark-text: #D0D0D0;
        --dark-text-light: #B0B0B0;
        --dark-text-muted: #888888;
        --dark-border: #3A3A3A;
        --dark-border-light: #4A4A4A;
        --dark-shadow: rgba(0, 0, 0, 0.4);
        --dark-shadow-light: rgba(0, 0, 0, 0.2);
        --dark-card: #252525;
        --dark-card-hover: #2D2D2D;
    }
    
    /* Main background - dark gradient */
    .stApp {
        background: linear-gradient(135deg, #1A1A1A 0%, #242424 50%, #2D2D2D 100%);
        min-height: 100vh;
        color: var(--dark-text);
    }
    
    /* Sidebar styling - dark theme */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #252525 0%, #1F1F1F 100%);
        border-right: 2px solid var(--dark-border);
        box-shadow: 2px 0 12px var(--dark-shadow);
        color: var(--dark-text);
        padding: 0.5rem 0.5rem 0.75rem 0.5rem !important;
    }
    
    /* Remove top spacing from sidebar content */
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebar"] .css-1d391kg,
    [data-testid="stSidebar"] > div > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove top margin from first element in sidebar */
    [data-testid="stSidebar"] .element-container:first-child,
    [data-testid="stSidebar"] .stMarkdown:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Remove top spacing from first heading */
    [data-testid="stSidebar"] h3:first-of-type {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Reduce spacing in sidebar sections */
    [data-testid="stSidebar"] .stMarkdown {
        margin-bottom: 0.25rem !important;
        margin-top: 0.25rem !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.5rem !important;
        margin-top: 0.25rem !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown h3 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.25rem !important;
        padding-bottom: 0.25rem !important;
    }
    
    [data-testid="stSidebar"] .element-container {
        margin-bottom: 0.5rem !important;
    }
    
    [data-testid="stSidebar"] hr {
        margin: 0.5rem 0 !important;
        border-width: 1px !important;
    }
    
    /* Reduce spacing between buttons */
    [data-testid="stSidebar"] .stButton {
        margin-bottom: 0.25rem !important;
    }
    
    /* Reduce spacing for status badges */
    [data-testid="stSidebar"] .status-badge {
        margin: 0.15rem !important;
    }
    
    /* Compact checkbox and radio spacing */
    [data-testid="stSidebar"] .stCheckbox,
    [data-testid="stSidebar"] .stRadio {
        margin-bottom: 0.5rem !important;
    }
    
    /* Reduce spacing for text inputs */
    [data-testid="stSidebar"] .stTextInput {
        margin-bottom: 0.5rem !important;
    }
    
    /* Reduce spacing for info boxes */
    [data-testid="stSidebar"] .stInfo,
    [data-testid="stSidebar"] .stSuccess,
    [data-testid="stSidebar"] .stWarning,
    [data-testid="stSidebar"] .stError {
        margin-bottom: 0.5rem !important;
        padding: 0.5rem !important;
    }
    
    /* Main content area - dark card background */
    .main .block-container {
        background: linear-gradient(135deg, rgba(37, 37, 37, 0.95) 0%, rgba(30, 30, 30, 0.95) 100%);
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px var(--dark-shadow);
        margin-top: 1rem;
        border: 1px solid var(--dark-border);
        color: var(--dark-text);
    }
    
    /* Headers */
    h1 {
        color: var(--dark-text) !important;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    h2, h3 {
        color: var(--dark-text) !important;
        font-weight: 600;
    }
    
    /* Ensure all headings have good contrast */
    h3 {
        color: var(--dark-text) !important;
        opacity: 1 !important;
    }
    
    /* Fix any markdown headings that might have low contrast */
    .stMarkdown h3,
    .main h3 {
        color: var(--dark-text) !important;
    }
    
    /* Buttons - primary */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--dark-primary) 0%, var(--dark-primary-dark) 100%);
        color: #E0E0E0;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(91, 155, 213, 0.3);
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(91, 155, 213, 0.4);
        background: linear-gradient(135deg, #6BA5D8 0%, #5B9BD5 100%);
        color: #E8E8E8;
    }
    
    /* Buttons - secondary (including refresh button) */
    .stButton > button:not([kind="primary"]),
    button[kind="secondary"],
    .stButton button {
        background: linear-gradient(135deg, #2D2D2D 0%, #252525 100%) !important;
        color: var(--dark-text) !important;
        border: 1.5px solid var(--dark-border) !important;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px var(--dark-shadow-light);
    }
    
    .stButton > button:not([kind="primary"]):hover,
    button[kind="secondary"]:hover,
    .stButton button:hover {
        background: linear-gradient(135deg, #353535 0%, #2D2D2D 100%) !important;
        border-color: var(--dark-primary) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px var(--dark-shadow);
        color: var(--dark-text) !important;
    }
    
    /* Text inputs and text areas */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #2D2D2D;
        border: 1.5px solid var(--dark-border);
        border-radius: 8px;
        padding: 0.5rem;
        transition: all 0.3s ease;
        box-shadow: inset 0 2px 4px var(--dark-shadow);
        color: var(--dark-text);
        caret-color: var(--dark-primary);
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        background: #333333;
        border-color: var(--dark-primary);
        box-shadow: 0 0 0 3px rgba(91, 155, 213, 0.2), inset 0 2px 4px var(--dark-shadow);
        color: var(--dark-text);
        caret-color: var(--dark-primary);
    }
    
    /* Ensure text cursor (caret) is visible in all inputs and textareas */
    input[type="text"],
    input[type="password"],
    textarea {
        caret-color: #5B9BD5 !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: var(--dark-text-muted);
    }
    
    /* Select boxes */
    .stSelectbox > div > div > select {
        background: #2D2D2D;
        border: 1.5px solid var(--dark-border);
        border-radius: 8px;
        box-shadow: inset 0 2px 4px var(--dark-shadow);
        color: var(--dark-text);
    }
    
    /* Info boxes and alerts */
    .stInfo {
        background-color: rgba(91, 155, 213, 0.15);
        border-left: 4px solid var(--dark-primary);
        border-radius: 6px;
        color: var(--dark-text);
    }
    
    .stSuccess {
        background-color: rgba(46, 204, 113, 0.15);
        border-left: 4px solid #2ECC71;
        border-radius: 6px;
        color: var(--dark-text);
    }
    
    .stWarning {
        background-color: rgba(255, 193, 7, 0.15);
        border-left: 4px solid #FFC107;
        border-radius: 6px;
        color: var(--dark-text);
    }
    
    .stError {
        background-color: rgba(231, 76, 60, 0.15);
        border-left: 4px solid #E74C3C;
        border-radius: 6px;
        color: var(--dark-text);
    }
    
    /* Radio buttons and checkboxes */
    .stRadio > div,
    .stCheckbox > div {
        background: linear-gradient(135deg, #2D2D2D 0%, #252525 100%);
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid var(--dark-border);
        box-shadow: 0 2px 4px var(--dark-shadow-light);
        color: var(--dark-text);
    }
    
    .stRadio > div > label,
    .stCheckbox > div > label {
        color: var(--dark-text);
    }
    
    /* Dividers */
    hr {
        border-color: var(--dark-border);
        margin: 1.5rem 0;
    }
    
    /* Markdown content */
    .stMarkdown {
        color: var(--dark-text);
        line-height: 1.6;
    }
    
    .stMarkdown p {
        color: var(--dark-text);
    }
    
    .stMarkdown code {
        background: #1F1F1F;
        color: var(--dark-accent);
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
    }
    
    /* Dataframes */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px var(--dark-shadow);
        background: #2D2D2D;
    }
    
    .stDataFrame table {
        background: #2D2D2D;
        color: var(--dark-text);
    }
    
    .stDataFrame th {
        background: #1F1F1F;
        color: var(--dark-text);
    }
    
    .stDataFrame td {
        background: #2D2D2D;
        color: var(--dark-text);
        border-color: var(--dark-border);
    }
    
    /* Sidebar buttons */
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #2D2D2D 0%, #252525 100%);
        border: 1.5px solid var(--dark-border);
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px var(--dark-shadow-light);
        color: var(--dark-text);
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #353535 0%, #2D2D2D 100%);
        border-color: var(--dark-primary);
        box-shadow: 0 4px 8px var(--dark-shadow);
        transform: translateX(2px);
        color: var(--dark-text);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: var(--dark-primary) transparent transparent transparent;
    }
    
    /* Badges and Status Indicators */
    .status-badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .badge-demo {
        background: linear-gradient(135deg, #4A3A3A 0%, #3A2A2A 100%);
        color: var(--dark-text-light);
        box-shadow: 0 2px 4px var(--dark-shadow);
        border: 1px solid var(--dark-border);
    }
    
    .badge-ai {
        background: linear-gradient(135deg, #3A4A5A 0%, #2A3A4A 100%);
        color: var(--dark-text-light);
        box-shadow: 0 2px 4px var(--dark-shadow);
        border: 1px solid var(--dark-border-light);
    }
    
    .badge-connected {
        background: linear-gradient(135deg, #2A4A3A 0%, #1A3A2A 100%);
        color: var(--dark-text-light);
        box-shadow: 0 2px 4px var(--dark-shadow);
        border: 1px solid var(--dark-border-light);
    }
    
    .badge-disconnected {
        background: #3A3A3A;
        color: var(--dark-text-muted);
        border: 1px solid var(--dark-border);
    }
    
    /* Breadcrumb Navigation */
    .breadcrumb {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
        padding: 0.75rem 1rem;
        background: linear-gradient(135deg, #2D2D2D 0%, #252525 100%);
        border-radius: 8px;
        border: 1px solid var(--dark-border);
        box-shadow: 0 2px 8px var(--dark-shadow);
    }
    
    .breadcrumb-item {
        color: var(--dark-text-light);
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .breadcrumb-item.active {
        color: var(--dark-primary);
        font-weight: 600;
    }
    
    .breadcrumb-separator {
        color: var(--dark-border-light);
        margin: 0 0.25rem;
    }
    
    /* Step Indicator */
    .step-indicator {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 1.5rem 0;
        padding: 1rem;
        background: linear-gradient(135deg, #2D2D2D 0%, #252525 100%);
        border-radius: 12px;
        border: 1px solid var(--dark-border);
        box-shadow: 0 2px 12px var(--dark-shadow);
    }
    
    .step-item {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
    }
    
    .step-item:not(:last-child)::after {
        content: '';
        position: absolute;
        top: 1.25rem;
        left: 60%;
        width: 80%;
        height: 2px;
        background: var(--dark-border);
        z-index: 0;
    }
    
    .step-item.completed:not(:last-child)::after {
        background: var(--dark-primary);
    }
    
    .step-number {
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        margin-bottom: 0.5rem;
        position: relative;
        z-index: 1;
        background: linear-gradient(135deg, #2D2D2D 0%, #252525 100%);
        border: 2px solid var(--dark-border);
        color: var(--dark-text-light);
        transition: all 0.3s ease;
        box-shadow: 0 2px 6px var(--dark-shadow);
    }
    
    .step-item.active .step-number {
        background: linear-gradient(135deg, #3A5A7A 0%, #2A4A6A 100%);
        color: var(--dark-text-light);
        border-color: var(--dark-primary);
        box-shadow: 0 2px 8px var(--dark-shadow);
        transform: scale(1.1);
    }
    
    .step-item.completed .step-number {
        background: linear-gradient(135deg, #2A5A4A 0%, #1A4A3A 100%);
        color: var(--dark-text-light);
        border-color: var(--dark-border-light);
    }
    
    .step-label {
        font-size: 0.85rem;
        font-weight: 500;
        color: var(--dark-text-light);
        text-align: center;
    }
    
    .step-item.active .step-label {
        color: var(--dark-primary);
        font-weight: 600;
    }
    
    /* Enhanced Typography */
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        letter-spacing: -0.01em;
    }
    
    h1 {
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    
    h2, h3 {
        letter-spacing: -0.01em;
        line-height: 1.3;
    }
    
    p {
        line-height: 1.7;
        color: var(--dark-text);
    }
    
    /* Card/Container Styling */
    .content-card {
        background: linear-gradient(135deg, #2D2D2D 0%, #252525 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid var(--dark-border);
        box-shadow: 0 2px 12px var(--dark-shadow);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        color: var(--dark-text);
    }
    
    .content-card:hover {
        background: linear-gradient(135deg, #353535 0%, #2D2D2D 100%);
        box-shadow: 0 4px 20px var(--dark-shadow);
        transform: translateY(-2px);
        border-color: var(--dark-primary);
    }
    
    /* Enhanced Input Groups */
    .input-group {
        margin-bottom: 1.5rem;
    }
    
    .input-group label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 600;
        color: var(--dark-text);
        font-size: 0.95rem;
    }
    
    /* Loading States */
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    
    /* Success Animation */
    @keyframes successPop {
        0% {
            transform: scale(0.8);
            opacity: 0;
        }
        50% {
            transform: scale(1.05);
        }
        100% {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    .success-animation {
        animation: successPop 0.4s ease-out;
    }
    
    /* Enhanced Spacing */
    .section-spacing {
        margin-top: 2rem;
        margin-bottom: 2rem;
    }
    
    /* Text Area Enhancements */
    .stTextArea > div > div > textarea {
        min-height: 120px;
        resize: vertical;
    }
    
    /* Enhanced Selectbox */
    .stSelectbox > div > div > select {
        cursor: pointer;
    }
    
    /* Tooltip Enhancements */
    [data-testid="stTooltipIcon"] {
        color: var(--dark-primary);
    }
    
    /* Sidebar Enhancements */
    [data-testid="stSidebar"] .stMarkdown h3 {
        margin-top: 1rem;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--dark-border);
        color: var(--dark-text);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: var(--dark-text);
    }
    
    /* Enhanced Radio Buttons */
    .stRadio > div > label {
        padding: 0.5rem;
        border-radius: 6px;
        transition: all 0.2s ease;
        color: var(--dark-text);
    }
    
    .stRadio > div > label:hover {
        background: linear-gradient(135deg, #353535 0%, #2D2D2D 100%);
    }
    
    /* Enhanced Checkbox */
    .stCheckbox > label {
        font-weight: 500;
        color: var(--dark-text);
    }
    
    /* Smooth Transitions */
    * {
        transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
    }
    
    /* Focus States */
    button:focus-visible,
    input:focus-visible,
    textarea:focus-visible,
    select:focus-visible {
        outline: 2px solid var(--dark-primary);
        outline-offset: 2px;
    }
    
    /* Streamlit default element overrides for dark theme */
    .stSelectbox label,
    .stTextInput label,
    .stTextArea label {
        color: var(--dark-text);
    }
    
    /* Code blocks */
    pre {
        background: #1F1F1F !important;
        color: var(--dark-text) !important;
        border: 1px solid var(--dark-border);
    }
    
    code {
        background: #1F1F1F;
        color: var(--dark-accent);
    }
    
    /* Streamlit header/deploy bar - dark theme */
    header[data-testid="stHeader"],
    .stApp > header {
        background: linear-gradient(135deg, #252525 0%, #1F1F1F 100%) !important;
        border-bottom: 1px solid var(--dark-border) !important;
    }
    
    header[data-testid="stHeader"] > div,
    .stApp > header > div {
        background: transparent !important;
    }
    
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] a,
    .stApp > header button,
    .stApp > header a {
        color: var(--dark-text-light) !important;
    }
    
    header[data-testid="stHeader"] button:hover,
    header[data-testid="stHeader"] a:hover,
    .stApp > header button:hover,
    .stApp > header a:hover {
        color: var(--dark-text) !important;
    }
    
    /* Hide or style the deploy button area */
    #MainMenu,
    [data-testid="stHeader"] {
        visibility: visible;
        background: linear-gradient(135deg, #252525 0%, #1F1F1F 100%) !important;
    }
    
    /* Style the hamburger menu */
    button[title="View app source"],
    button[title="Get help"],
    button[title="Deploy"],
    [data-testid="stHeader"] button {
        background: transparent !important;
        color: var(--dark-text-light) !important;
    }
    
    [data-testid="stHeader"] button:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        color: var(--dark-text) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Inject styles on app load
inject_warm_styles()

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "input"
if "research_data" not in st.session_state:
    st.session_state.research_data = {}
if "hypothesis" not in st.session_state:
    st.session_state.hypothesis = None
if "personas" not in st.session_state:
    st.session_state.personas = []
if "selected_persona" not in st.session_state:
    st.session_state.selected_persona = None
if "sequence" not in st.session_state:
    st.session_state.sequence = None
if "sequences" not in st.session_state:
    st.session_state.sequences = {}  # lane_id -> content (scalable sequences by persona lane)
if "selected_lanes" not in st.session_state:
    st.session_state.selected_lanes = []  # list of lane ids user chose (1-3)
if "current_sequence_lane_id" not in st.session_state:
    st.session_state.current_sequence_lane_id = None  # which lane's sequence is displayed
if "prospect_info" not in st.session_state:
    st.session_state.prospect_info = {}
if "ae_handoff" not in st.session_state:
    st.session_state.ae_handoff = None


def get_openai_client():
    """Get OpenAI client with API key from Streamlit secrets, env, or sidebar."""
    api_key = _get_openai_key()
    if api_key:
        return OpenAI(api_key=api_key)
    return None


def list_available_gemini_models():
    """List available Gemini models for debugging."""
    if not GEMINI_AVAILABLE:
        return []
    api_key = _get_gemini_key()
    if not api_key:
        return []
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        available = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                available.append(model.name)
        return available
    except Exception as e:
        return []


def get_gemini_client():
    """Get Gemini client with API key from Streamlit secrets, env, or sidebar."""
    if not GEMINI_AVAILABLE:
        return None
    api_key = _get_gemini_key()
    if api_key:
        genai.configure(api_key=api_key)
        # Try different model names in order of preference
        model_names = [
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-pro',
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro',
            'models/gemini-pro'
        ]
        
        # First, try to list available models and use the first one that supports generateContent
        try:
            models = genai.list_models()
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    # Extract model name (remove 'models/' prefix if present)
                    model_name = model.name.replace('models/', '')
                    return genai.GenerativeModel(model_name)
        except:
            pass
        
        # Fallback: try model names directly
        for model_name in model_names:
            try:
                return genai.GenerativeModel(model_name)
            except:
                continue
        
        # If all else fails, try the first one and let it error
        return genai.GenerativeModel('gemini-1.5-flash')
    return None


def get_ai_provider():
    """Get the selected AI provider from session state."""
    return st.session_state.get("ai_provider", "gemini")  # Default to Gemini


def generate_demo_hypothesis(research_data: dict) -> str:
    """Generate a realistic demo hypothesis without API calls."""
    company_info = research_data.get("company_info", "").lower()
    job_postings = research_data.get("job_postings", "").lower()
    news_signals = research_data.get("news_signals", "").lower()
    
    # Extract company name if possible
    company_name = "this company"
    if company_info:
        lines = company_info.split("\n")
        for line in lines[:3]:
            if "company" in line or "inc" in line or "corp" in line or "ltd" in line:
                company_name = line.split()[0] if line.split() else "this company"
                break
    
    # Detect signals
    has_funding = "funding" in news_signals or "raised" in news_signals or "series" in news_signals
    has_hiring = "hiring" in job_postings or "engineer" in job_postings or "developer" in job_postings
    has_devex = "devex" in job_postings or "developer experience" in job_postings or "platform" in job_postings
    
    hypothesis = f"""## Why This Account

{company_name.title()} appears to be a strong fit for Cursor based on several indicators:

**Company Scale & Engineering Focus:**
- Based on the research provided, this organization demonstrates significant engineering investment
- The presence of relevant job postings suggests an active, growing engineering organization
- This indicates the scale necessary to benefit from AI-powered developer productivity tools

**Tech Stack & Digital Maturity:**
- The research suggests a modern, engineering-forward culture
- Active hiring in technical roles indicates ongoing investment in engineering capabilities
- This aligns with Cursor's ideal customer profile of companies prioritizing developer experience

**Budget Indicators:**
{f"- Recent funding activity suggests budget availability for developer tooling investments" if has_funding else "- Growth indicators suggest potential budget for productivity tools"}

---

## Why Now

Several timely signals create urgency for outreach:

**Immediate Triggers:**
{f"- Active hiring in engineering roles - perfect timing to introduce productivity tools as teams scale" if has_hiring else "- Engineering team growth creates opportunity for productivity improvements"}
{f"- Platform/DevEx team formation or expansion indicates focus on developer experience" if has_devex else "- Active engineering investment suggests openness to productivity solutions"}

**Pain Points Likely Experienced:**
- Scaling engineering teams while maintaining velocity
- Onboarding new developers efficiently
- Managing context-switching and productivity bottlenecks
- Justifying engineering headcount growth to leadership

**Connection to Cursor Value Props:**
- Cursor's 2-3x velocity improvement directly addresses scaling challenges
- Codebase understanding accelerates onboarding for new team members
- AI-powered development helps teams ship faster without proportional headcount increases

---

## Proof Points / Evidence to Cite
- Relevant job postings (e.g. Platform Engineering, DevEx roles) — include URL if pasted in research
- Engineering headcount or scale indicators from research
- Recent funding, product launch, or conference mentions — include URL/source if in research
- Any specific stats or quotes from the research (e.g. "300+ apps", "1B uses")

---

## Tech Stack
- List any languages, frameworks, infrastructure, or tools mentioned in the research
- If not specified: "Not specified in research"

---

## Risks / Why We Might Lose
- Existing AI coding tool commitment (name a specific competitor only if the research indicates which one)
- Budget or timing constraints
- Other disqualifiers suggested by the research (avoid generic "lengthy enterprise security review")
"""
    
    return hypothesis


def generate_demo_sequence(lane: dict, hypothesis: str, prospect_info: dict) -> str:
    """Generate a realistic demo sequence without API calls. lane = dict with id, name, example_titles, hook, cursor_play, peer_pivot."""
    first_name = prospect_info.get('first_name') or '[First Name]'
    company = prospect_info.get('company') or '[Company]'
    lane_name = lane.get("name", "Internal Tool Owners")
    
    sequence = f"""# Outbound Sequence — {lane_name}

## Sequence Overview
**Persona lane:** {lane_name}
**Total Steps:** 8
**Duration:** 14 days
**Channels:** Email, LinkedIn, Phone

---

## Step 1: Initial Email (Day 1)
**Type:** Email
**Subject:** Your DevEx team caught my attention

**Body:**

Hi {first_name},

I noticed {company} is building out your developer experience function - saw the Platform Engineering role you're hiring for.

At similar companies, we've seen DevEx teams struggle with developer tool adoption. Teams try new tools, but they don't stick because they don't understand the full codebase context.

Cursor is different - it's an AI code editor built from the ground up with codebase understanding. When developers ask questions about your authentication system across 50 files, Cursor actually knows the answer.

Quick question: What's your biggest challenge with developer productivity right now?

Best,
[Your Name]

---

## Step 2: LinkedIn Connection (Day 2)
**Type:** LinkedIn
**Message:**

Hi {first_name}, I saw your role at {company} and thought you might be interested in connecting. I work with engineering leaders on developer productivity - would love to share what I'm seeing in the market.

---

## Step 3: Follow-up Email (Day 4)
**Type:** Email
**Subject:** Re: Your DevEx team caught my attention

**Body:**

Hi {first_name},

Following up on my note about developer productivity at {company}.

One thing I didn't mention: Cursor is built on VS Code, so your developers can start using it immediately with zero learning curve. All their extensions, settings, and workflows work exactly the same.

We've seen 90%+ adoption in the first 30 days at companies like yours - developers actually ask for it.

Worth a 15-minute conversation?

Best,
[Your Name]

---

## Step 4: LinkedIn Message (Day 5)
**Type:** LinkedIn
**Message:**

{first_name}, curious - are you evaluating any AI coding tools for your team? Seeing a lot of interest from DevEx leaders right now.

---

## Step 5: Value Email (Day 7)
**Type:** Email
**Subject:** Quick question about {company}'s engineering velocity

**Body:**

Hi {first_name},

I've been thinking about the scaling challenges you're likely facing as you grow the engineering team.

One thing we hear consistently: teams using Cursor report 2-3x faster development velocity. Not just autocomplete - actual codebase understanding that helps with refactoring, debugging, and onboarding.

If you're open to it, I'd love to show you a quick demo on your actual codebase. Takes 15 minutes and you'll see the difference immediately.

Does next week work for a brief call?

Best,
[Your Name]

---

## Step 6: Phone Call Attempt (Day 9)
**Type:** Phone
**Opener:**

Hi {first_name}, this is [Your Name] from Cursor. I've been emailing you about developer productivity tools - do you have 2 minutes?

**If voicemail:**
Hi {first_name}, this is [Your Name] from Cursor. I've been reaching out about AI-powered developer productivity tools. I noticed {company} is investing heavily in engineering, and I thought you'd be interested in what we're seeing - teams using Cursor are shipping 2-3x faster. Would love to connect - my number is [phone]. Talk soon.

---

## Step 7: Final Email (Day 11)
**Type:** Email
**Subject:** Last try - developer productivity at {company}

**Body:**

Hi {first_name},

I know you're busy, so I'll keep this short.

{company} is clearly investing in engineering - the Platform Engineering role you're hiring for is proof of that. The question is: are your developers as productive as they could be?

Cursor helps engineering teams ship faster without adding headcount. It's what GitHub Copilot would be if it understood your entire codebase.

If this isn't the right time, no worries. But if you're curious, I'm happy to show you what it looks like in action.

Best,
[Your Name]

---

## Step 8: Breakup Email (Day 14)
**Type:** Email
**Subject:** Closing the loop

**Body:**

Hi {first_name},

Haven't heard back, so I'll assume this isn't a priority right now. That's totally fine - timing matters.

If that changes, or if you'd like to stay in touch for when it makes sense, just let me know.

Best of luck with the engineering growth at {company}.

Best,
[Your Name]

---

## Personalization Notes
- Reference specific job postings or team formations from research
- Connect to actual pain points mentioned in hypothesis
- Adjust messaging based on persona's likely concerns
- Use company-specific signals throughout sequence
"""
    
    return sequence


def load_file(filepath: str) -> str:
    """Load a file from the project directory."""
    file_path = Path(__file__).parent / filepath
    if file_path.exists():
        return file_path.read_text()
    return ""


def load_kb_files() -> dict:
    """Load knowledge base files if they exist."""
    kb_files = {
        "cursor_encyclopedia": "kb/cursor_encyclopedia.md",
        "voice": "kb/voice.md",
        "offers": "kb/offers.md",
        "sequence_patterns": "kb/sequence_patterns.md",
        "personalization": "kb/personalization_playbook.md"
    }
    
    kb_content = {}
    for key, filepath in kb_files.items():
        content = load_file(filepath)
        if content:
            kb_content[key] = content
    
    return kb_content


def load_persona_lanes() -> list:
    """Load and parse persona lanes from kb/persona_lanes.md. Returns list of dicts with id, name, example_titles, hook, cursor_play, peer_pivot (optional)."""
    content = load_file("kb/persona_lanes.md")
    if not content:
        return []
    lanes = []
    # Split by ## N. (e.g. ## 1. Big Picture Leaders)
    blocks = re.split(r"\n##\s+(\d+)\.\s+", content)[1:]  # skip intro before first ##
    for i in range(0, len(blocks), 2):
        if i + 1 >= len(blocks):
            break
        num, rest = blocks[i], blocks[i + 1]
        name_line = rest.split("\n")[0].strip()
        name = name_line.split("**")[0].strip() or name_line
        text = rest

        def _extract(label: str) -> str:
            m = re.search(r"\*\*" + re.escape(label) + r"\*\*[:\s]*(.*?)(?=\n\*\*|\n---|\Z)", text, re.DOTALL)
            return m.group(1).strip() if m else ""

        lanes.append({
            "id": num,
            "name": name,
            "example_titles": _extract("Example titles"),
            "hook": _extract("Hook"),
            "cursor_play": _extract("Cursor play"),
            "peer_pivot": _extract("Peer pivot") or ""
        })
    return lanes


def generate_hypothesis_with_ai(prompt: str, provider: str) -> str:
    """Generate text using the specified AI provider."""
    if provider == "gemini":
        model = get_gemini_client()
        if not model:
            raise Exception("Gemini API key not configured")
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=6144,
                )
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            # Check for rate limit errors
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                raise Exception("RATE_LIMIT")
            raise e
    else:  # OpenAI
        client = get_openai_client()
        if not client:
            raise Exception("OpenAI API key not configured")
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert B2B sales strategist. Generate a complete, actionable outbound hypothesis. Always finish every section and sentence—do not stop mid-sentence or omit sections. You MUST include all five sections including Tech Stack and Risks."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=6144
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            # Check for quota/authentication errors
            if "quota" in error_msg.lower() or "insufficient" in error_msg.lower() or "429" in error_msg:
                raise Exception("QUOTA_EXCEEDED")
            raise e


def generate_hypothesis(research_data: dict, use_demo: bool = False) -> str:
    """Generate outbound hypothesis using AI or demo mode."""
    # Check if demo mode is enabled
    if use_demo or st.session_state.get("demo_mode", False):
        return generate_demo_hypothesis(research_data)
    
    provider = get_ai_provider()
    
    # Load prompts
    cursor_context = load_file("prompts/cursor_context.md")
    hypothesis_template = load_file("prompts/hypothesis.md")
    
    # Load knowledge base files (for personalization guidance)
    kb_content = load_kb_files()
    
    # Build the prompt
    prompt = hypothesis_template.replace("{{company_info}}", research_data.get("company_info", "Not provided"))
    prompt = prompt.replace("{{job_postings}}", research_data.get("job_postings", "Not provided"))
    prompt = prompt.replace("{{linkedin_profiles}}", research_data.get("linkedin_profiles", "Not provided"))
    prompt = prompt.replace("{{news_signals}}", research_data.get("news_signals", "Not provided"))
    prompt = prompt.replace("{{cursor_context}}", cursor_context)
    
    # Inject KB content if available (Cursor encyclopedia + personalization for hypothesis quality)
    if kb_content.get("cursor_encyclopedia"):
        prompt += "\n\n## Cursor Technical & Competitive Context\n\n" + kb_content["cursor_encyclopedia"] + "\n\n"
    if kb_content.get("personalization"):
        prompt += "\n\n## Personalization Guidelines\n\n" + kb_content["personalization"] + "\n\n"
    
    # Add system context for Gemini (which doesn't have separate system messages)
    if provider == "gemini":
        prompt = f"You are an expert B2B sales strategist. Generate a complete, actionable outbound hypothesis. Always finish every section and sentence—do not stop mid-sentence or omit sections. You MUST include all five sections including Tech Stack and Risks.\n\n{prompt}"
    
    try:
        return generate_hypothesis_with_ai(prompt, provider)
    except Exception as e:
        error_msg = str(e)
        if "QUOTA_EXCEEDED" in error_msg or "RATE_LIMIT" in error_msg:
            st.warning(f"⚠️ **API Quota/Rate Limit Exceeded**: Switching to demo mode.")
            return generate_demo_hypothesis(research_data)
        # Show actual error so user can see invalid key, permission, etc.
        st.error(f"⚠️ **API Error**: {error_msg[:500]}")
        st.info("Switching to demo mode. If this is an auth/key error, check Streamlit Secrets (GEMINI_API_KEY) and redeploy.")
        if provider == "openai":
            try:
                st.session_state.ai_provider = "gemini"
                return generate_hypothesis_with_ai(prompt, "gemini")
            except:
                return generate_demo_hypothesis(research_data)
        return generate_demo_hypothesis(research_data)


def extract_personas_from_hypothesis(hypothesis: str) -> list:
    """Extract persona recommendations from the hypothesis."""
    # Check for demo mode
    if st.session_state.get("demo_mode", False):
        return ["VP/Director of Engineering", "Platform/DevEx Engineering Lead", "CTO"]
    
    provider = get_ai_provider()
    prompt = f"Extract the recommended target personas from this sales hypothesis. Return ONLY a Python list of job titles, nothing else. Example: [\"VP Engineering\", \"DevEx Lead\", \"CTO\"]\n\n{hypothesis}"
    
    try:
        if provider == "gemini":
            model = get_gemini_client()
            if model:
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0,
                        max_output_tokens=200,
                    )
                )
                content = response.text.strip()
        else:  # OpenAI
            client = get_openai_client()
            if not client:
                raise Exception("No API key")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Extract the recommended target personas from this sales hypothesis. Return ONLY a Python list of job titles, nothing else. Example: [\"VP Engineering\", \"DevEx Lead\", \"CTO\"]"},
                    {"role": "user", "content": hypothesis}
                ],
                temperature=0,
                max_tokens=200
            )
            content = response.choices[0].message.content.strip()
        
        # Try to evaluate as a Python list
        import ast
        personas = ast.literal_eval(content)
        if isinstance(personas, list) and len(personas) > 0:
            return personas
    except:
        pass
    
    # Fallback - try to extract from hypothesis text
    personas = []
    if "VP" in hypothesis or "Director" in hypothesis:
        personas.append("VP/Director of Engineering")
    if "Platform" in hypothesis or "DevEx" in hypothesis:
        personas.append("Platform/DevEx Engineering Lead")
    if "CTO" in hypothesis:
        personas.append("CTO")
    
    return personas if personas else ["VP/Director of Engineering", "Platform/DevEx Engineering Lead", "CTO"]


def generate_sequence(lane: dict, hypothesis: str, prospect_info: dict, use_demo: bool = False, reference_customers: str = "") -> str:
    """Generate outbound sequence for a persona lane (scalable across prospects). lane = dict with id, name, example_titles, hook, cursor_play, peer_pivot. reference_customers = optional list of current customers to cite in 1-2 steps."""
    # Check if demo mode is enabled
    if use_demo or st.session_state.get("demo_mode", False):
        return generate_demo_sequence(lane, hypothesis, prospect_info)
    
    provider = get_ai_provider()
    
    # Load templates
    cursor_context = load_file("prompts/cursor_context.md")
    sequence_template = load_file("prompts/sequence.md")
    sequence_structure = load_file("templates/sequence_structure.md")
    
    # Load knowledge base files
    kb_content = load_kb_files()
    
    # Build prospect context: use placeholders if no prospect provided
    has_prospect = prospect_info.get("first_name") and prospect_info.get("company")
    if has_prospect:
        prospect_context = f"""
Prospect (for this draft):
- Name: {prospect_info.get('first_name', '')} {prospect_info.get('last_name', '').strip() or ''}
- Title: {prospect_info.get('title', lane.get('name', ''))}
- Company: {prospect_info.get('company', '')}
- Email: {prospect_info.get('email', '') or 'unknown@company.com'}
"""
    else:
        prospect_context = """
No specific prospect—use placeholders so this sequence can scale:
- Use [First Name] where you would use their first name
- Use [Company] where you would use their company name
- Keep tone and messaging tailored to this persona lane; they can fill in details when they use it
"""
    
    peer_pivot_block = ""
    if lane.get("peer_pivot"):
        peer_pivot_block = "\n**Peer pivot (optional):** " + lane["peer_pivot"]
    
    # Build the prompt
    prompt = sequence_template.replace("{{persona_lane_name}}", lane.get("name", ""))
    prompt = prompt.replace("{{persona_lane_titles}}", lane.get("example_titles", ""))
    prompt = prompt.replace("{{persona_lane_hook}}", lane.get("hook", ""))
    prompt = prompt.replace("{{persona_lane_play}}", lane.get("cursor_play", ""))
    prompt = prompt.replace("{{persona_lane_peer_pivot}}", peer_pivot_block)
    prompt = prompt.replace("{{prospect_context}}", prospect_context)
    prompt = prompt.replace("{{hypothesis}}", hypothesis)
    # Reference customers: from Research Input, or from kb/reference_customers.md if field empty
    ref_customers = (reference_customers or "").strip()
    if not ref_customers:
        ref_customers = (load_file("kb/reference_customers.md") or "").strip()
    ref_block = ref_customers if ref_customers else "None provided—do not add customer references to the sequence."
    prompt = prompt.replace("{{reference_customers}}", ref_block)
    prompt = prompt.replace("{{sequence_template}}", sequence_structure)
    prompt = prompt.replace("{{cursor_context}}", cursor_context)
    
    # Inject knowledge base content if available
    kb_section = ""
    if kb_content:
        kb_section = "\n\n## Knowledge Base & Style Guide\n\n"
        if "cursor_encyclopedia" in kb_content:
            kb_section += "### Cursor Technical & Competitive Encyclopedia\n" + kb_content["cursor_encyclopedia"] + "\n\n"
        if "voice" in kb_content:
            kb_section += "### Voice & Style Guide\n" + kb_content["voice"] + "\n\n"
        if "offers" in kb_content:
            kb_section += "### Offer Library\n" + kb_content["offers"] + "\n\n"
        if "sequence_patterns" in kb_content:
            kb_section += "### Sequence Patterns\n" + kb_content["sequence_patterns"] + "\n\n"
        if "personalization" in kb_content:
            kb_section += "### Personalization Playbook\n" + kb_content["personalization"] + "\n\n"
        kb_section += "---\n\n**CRITICAL**: The content above (Cursor encyclopedia, voice, offers, sequence patterns, personalization) is the PRIMARY source for wording, Cursor-specific claims, and style. Use it exactly. The persona lane (hook / Cursor play) only orients the angle for this audience—it must not override or replace the sharper messaging in this KB. Every email and LinkedIn message must end with a CTA (question preferred). Vary openers—do not use the same opener phrase more than once in the sequence.\n\n"
    
    prompt = prompt + kb_section
    
    # Add system context for Gemini
    if provider == "gemini":
        prompt = f"You are an expert B2B sales copywriter. Generate the COMPLETE outbound sequence. You MUST include every step through Day 15 breakup (core) and Day 9 (LinkedIn-only). Do not stop early or omit any step.\n\n{prompt}"
    
    try:
        if provider == "gemini":
            model = get_gemini_client()
            if not model:
                raise Exception("Gemini API key not configured")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                )
            )
            return response.text
        else:  # OpenAI
            client = get_openai_client()
            if not client:
                raise Exception("OpenAI API key not configured")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert B2B sales copywriter. Generate the COMPLETE outbound sequence. You MUST include every step through Day 15 breakup (core) and Day 9 (LinkedIn-only). Do not stop early or omit any step."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=8192
            )
            return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        is_quota = "quota" in error_msg.lower() or "insufficient" in error_msg.lower() or "429" in error_msg or "RATE_LIMIT" in str(e) or "resource_exhausted" in error_msg.lower()
        if is_quota:
            st.warning("⚠️ **API Quota/Rate Limit Exceeded**: Switching to demo mode.")
            return generate_demo_sequence(lane, hypothesis, prospect_info)
        st.error(f"⚠️ **API Error**: {error_msg[:500]}")
        st.info("Switching to demo mode. If this is an auth/key error, check Streamlit Secrets (GEMINI_API_KEY) and redeploy.")
        if provider == "openai":
            st.info("🔄 OpenAI failed, trying Gemini...")
            try:
                st.session_state.ai_provider = "gemini"
                model = get_gemini_client()
                if model:
                    response = model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.7,
                            max_output_tokens=8192,
                        )
                    )
                    return response.text
            except:
                st.warning("⚠️ Both providers failed. Switching to demo mode.")
                return generate_demo_sequence(lane, hypothesis, prospect_info)
        st.warning("⚠️ **API Error**: Switching to demo mode.")
        return generate_demo_sequence(lane, hypothesis, prospect_info)


def generate_ae_handoff(hypothesis: str) -> str:
    """Generate AE handoff note + filled-in first call agenda from the hypothesis."""
    provider = get_ai_provider()
    handoff_template = load_file("prompts/ae_handoff_template.md")
    agenda_template = load_file("prompts/agenda_template.md")
    if not handoff_template or not agenda_template:
        return "Missing templates: ae_handoff_template.md or agenda_template.md"
    prompt = f"""You are an expert sales strategist. Using ONLY the hypothesis below, generate two artifacts:

1. **AE Handoff Note** – Follow the structure and instructions in the handoff template. Fill every section using only details from the hypothesis. Match the tone and depth of the Canva example in the template.

2. **First Call Agenda** – Follow the agenda template. Fill in every section marked "[Fill from hypothesis]" or with placeholders like [N], [API/product], [vertical], [challenge], [outcome], [Platform Engineering / relevant] using only the hypothesis. Keep all other wording from the template as written.

Do not invent information. Use only what is in the hypothesis.

---
## Handoff Template (structure to follow)
{handoff_template}

---
## Agenda Template (structure to follow, fill placeholders from hypothesis)
{agenda_template}

---
## Hypothesis (your only source)
{hypothesis}

---
Output your response in two clear sections with headers:
## AE Handoff Note
[full handoff note]

## First Call Agenda
[full filled-in agenda]

**Critical:** Complete BOTH sections in full. Do not stop mid-sentence or omit the First Call Agenda. If you run out of space, prioritize finishing the agenda.
"""
    try:
        if provider == "gemini":
            model = get_gemini_client()
            if not model:
                raise Exception("Gemini API key not configured")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.5,
                    max_output_tokens=8192,
                )
            )
            return response.text.strip()
        else:
            client = get_openai_client()
            if not client:
                raise Exception("OpenAI API key not configured")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert sales strategist. Generate an AE handoff note and filled-in first call agenda using ONLY the provided hypothesis. Follow the templates exactly. Do not invent information. You MUST complete both sections in full—do not stop early or omit the First Call Agenda."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=8192
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating AE handoff: {str(e)}"


def parse_sequence_to_csv(sequence: str, prospect_info: dict) -> pd.DataFrame:
    """Parse the generated sequence into CSV format for Outreach.io."""
    provider = get_ai_provider()
    
    # Count steps in the sequence to validate extraction
    step_count = sequence.count("## Step") or sequence.count("Step ")
    
    csv_prompt = f"""
Convert this outbound sequence into a structured CSV format. Extract EVERY SINGLE STEP and return ONLY valid CSV data with these exact columns:
step_number,step_day,step_type,subject,body

CRITICAL REQUIREMENTS:
- The core sequence has 12 steps: Day 1 (email, LinkedIn connect, call), Day 3 (email, call), Day 5 (email, call), Day 8 (email), Day 9 (call), Day 11 (email), Day 12 (call), Day 15 (breakup email). Extract ALL 12 steps.
- There may also be a separate "LinkedIn only" sequence (Day 1, 3, 5, 9). Include those steps too if present, so the CSV can have 12 or more rows for the core sequence.
- Do NOT stop at step 9. You MUST include steps 10, 11, 12 (Day 11 email, Day 12 call, Day 15 breakup).
- Count the steps in the sequence and ensure the CSV has a row for every single one.

Rules:
- step_number: 1, 2, 3, ... (numeric only, sequential)
- step_day: Extract the day number from each step (e.g., "Day 1" = 1, "Day 15" = 15)
- step_type: Email, LinkedIn, or Phone (exact values, case-sensitive)
- subject: Email subject line (leave empty for LinkedIn/Phone steps)
- body: The full message content (for phone, include opener and voicemail script)

IMPORTANT CSV FORMATTING RULES:
- Use double quotes to wrap fields that contain commas, newlines, or quotes
- Escape any double quotes inside fields by doubling them ("" becomes "")
- Do NOT include any markdown code blocks (no ```)
- Do NOT include any explanations or text before/after the CSV
- Start immediately with the header row: step_number,step_day,step_type,subject,body
- Each row must be on a single line (use \\n for newlines within body field)
- Ensure all rows have the same number of columns
- Include ALL 12 core steps minimum. Do not truncate.

Return ONLY the raw CSV data, nothing else.

Sequence to convert:
{sequence}
"""
    
    csv_content = None
    try:
        if provider == "gemini":
            model = get_gemini_client()
            if not model:
                st.error("Gemini API key not configured for CSV export")
                return pd.DataFrame()
            response = model.generate_content(
                f"You are a data formatter. Convert sequences to clean CSV format. Extract ALL 12 core steps (through Day 15 breakup). Do not stop at step 9.\n\n{csv_prompt}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0,
                    max_output_tokens=8192,
                )
            )
            csv_content = response.text.strip()
        else:  # OpenAI
            client = get_openai_client()
            if not client:
                st.error("OpenAI API key not configured for CSV export")
                return pd.DataFrame()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a data formatter. Convert sequences to clean CSV format. Extract ALL 12 core steps (through Day 15 breakup). Do not stop at step 9 or skip any steps."},
                    {"role": "user", "content": csv_prompt}
                ],
                temperature=0,
                max_tokens=8192
            )
            csv_content = response.choices[0].message.content.strip()
        
        # Remove any markdown code blocks
        if csv_content.startswith("```"):
            # Extract content from code block
            lines = csv_content.split("\n")
            # Find the first line that's not ``` or language identifier
            start_idx = 1
            if len(lines) > 1 and lines[1].strip() and not lines[1].strip().startswith("```"):
                start_idx = 1
            else:
                start_idx = 2
            # Find the last ```
            end_idx = len(lines) - 1
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == "```":
                    end_idx = i
                    break
            csv_content = "\n".join(lines[start_idx:end_idx])
        
        # Clean up the CSV content
        csv_content = csv_content.strip()
        
        # Remove any leading/trailing non-CSV content (explanations, etc.)
        lines = csv_content.split("\n")
        # Find the header row (should contain step_number, step_day, etc.)
        header_idx = 0
        for i, line in enumerate(lines):
            if "step_number" in line.lower() and "step_day" in line.lower():
                header_idx = i
                break
        csv_content = "\n".join(lines[header_idx:])
        
        # Try to fix common CSV issues
        # Replace smart quotes with regular quotes
        csv_content = csv_content.replace('"', '"').replace('"', '"')
        csv_content = csv_content.replace(''', "'").replace(''', "'")
        
        # Parse CSV with more lenient options
        df = None
        parse_error = None
        try:
            # First try: standard pandas CSV parsing (default settings work best for most cases)
            df = pd.read_csv(io.StringIO(csv_content), on_bad_lines='skip')
        except Exception as e1:
            parse_error = str(e1)
            try:
                # Second try: explicitly set quotechar
                df = pd.read_csv(io.StringIO(csv_content), quotechar='"', on_bad_lines='skip')
            except Exception as e2:
                try:
                    # Third try: use engine='python' which is more lenient with malformed CSV
                    df = pd.read_csv(io.StringIO(csv_content), engine='python', on_bad_lines='skip', quotechar='"')
                except Exception as e3:
                    try:
                        # Fourth try: use QUOTE_ALL (quoting=1) which handles all fields
                        df = pd.read_csv(io.StringIO(csv_content), quoting=1, on_bad_lines='skip')
                    except Exception as e4:
                        # If all parsing attempts fail, raise with context
                        raise Exception(f"CSV parsing failed. Last error: {str(e4)}. Raw CSV content (first 500 chars): {csv_content[:500]}")
        
        if df is None or df.empty:
            raise Exception(f"Failed to parse CSV. Error: {parse_error}. Raw CSV content (first 500 chars): {csv_content[:500]}")
        
        # Validate that we captured all steps
        # Count steps in the original sequence using multiple patterns
        step_patterns = [
            r'## Step \d+',
            r'Step \d+:',
            r'Step \d+ ',
            r'Step \d+\.'  # For "Step 1." format
        ]
        step_matches = []
        for pattern in step_patterns:
            matches = re.findall(pattern, sequence, re.IGNORECASE)
            if matches:
                # Extract step numbers from matches
                step_nums = [int(re.search(r'\d+', m).group()) for m in matches if re.search(r'\d+', m)]
                step_matches.extend(step_nums)
        
        sequence_max_step = max(step_matches) if step_matches else 0
        sequence_step_count = len(set(step_matches)) if step_matches else 0
        
        # Count steps in the parsed CSV
        csv_step_count = len(df)
        
        # Check if step_number column exists and validate sequential steps
        if 'step_number' in df.columns:
            max_step = int(df['step_number'].max()) if not df['step_number'].isna().all() else 0
            min_step = int(df['step_number'].min()) if not df['step_number'].isna().all() else 0
            
            # Check for missing steps
            if max_step > csv_step_count:
                st.warning(f"⚠️ **Warning**: CSV has {csv_step_count} rows but step numbers go up to {max_step}. Some steps may be missing.")
            elif sequence_max_step > 0 and max_step < sequence_max_step:
                st.warning(f"⚠️ **Warning**: Sequence has steps up to {sequence_max_step} but CSV only goes up to step {max_step}. Missing steps: {', '.join([str(i) for i in range(max_step + 1, sequence_max_step + 1)])}")
            elif csv_step_count < sequence_step_count:
                st.warning(f"⚠️ **Warning**: Sequence appears to have {sequence_step_count} steps but CSV only has {csv_step_count} rows. Some steps may be missing.")
            
            # Check for gaps in step numbers
            if max_step > 0:
                expected_steps = set(range(min_step, max_step + 1))
                actual_steps = set(df['step_number'].dropna().astype(int))
                missing_steps = expected_steps - actual_steps
                if missing_steps:
                    st.warning(f"⚠️ **Warning**: Missing step numbers in CSV: {', '.join([str(s) for s in sorted(missing_steps)])}")
        
        # Add prospect info columns
        df['email'] = prospect_info.get('email', '')
        df['first_name'] = prospect_info.get('first_name', '')
        df['last_name'] = prospect_info.get('last_name', '')
        df['title'] = prospect_info.get('title', '')
        df['company'] = prospect_info.get('company', '')
        df['sequence_name'] = f"Cursor Outbound - {prospect_info.get('company', 'Unknown')}"
        
        # Reorder columns
        cols = ['email', 'first_name', 'last_name', 'title', 'company', 'sequence_name', 
                'step_number', 'step_day', 'step_type', 'subject', 'body']
        df = df[[c for c in cols if c in df.columns]]
        
        return df
    except Exception as e:
        error_msg = str(e)
        # If it's a model not found error, show available models
        if "404" in error_msg and "models/" in error_msg:
            available_models = list_available_gemini_models()
            if available_models:
                st.error(f"Error parsing sequence to CSV: {error_msg}")
                st.info(f"**Available Gemini models:** {', '.join(available_models)}")
            else:
                st.error(f"Error parsing sequence to CSV: {error_msg}")
                st.info("💡 **Tip**: Try switching to OpenAI in the sidebar, or check your Gemini API key.")
        else:
            st.error(f"Error parsing sequence to CSV: {error_msg}")
            # Show raw CSV content for debugging if available
            if csv_content:
                with st.expander("🔍 Debug: View raw CSV content from AI"):
                    st.code(csv_content, language="text")
                    st.info("💡 **Tip**: The AI may have generated malformed CSV. Try regenerating the sequence or switch to OpenAI provider.")
        return pd.DataFrame()


def render_breadcrumb(current_page: str):
    """Render breadcrumb navigation."""
    pages = {
        "input": "Research Input",
        "hypothesis": "Hypothesis",
        "sequence": "Sequence Builder",
        "ae_handoff": "AE Handoff"
    }
    
    breadcrumb_html = '<div class="breadcrumb">'
    breadcrumb_html += '<span class="breadcrumb-item">Home</span>'
    
    if current_page != "input":
        breadcrumb_html += '<span class="breadcrumb-separator">›</span>'
        if current_page == "ae_handoff":
            breadcrumb_html += '<span class="breadcrumb-item">Research Input</span>'
            breadcrumb_html += '<span class="breadcrumb-separator">›</span>'
            breadcrumb_html += '<span class="breadcrumb-item">Hypothesis</span>'
            breadcrumb_html += '<span class="breadcrumb-separator">›</span>'
            breadcrumb_html += '<span class="breadcrumb-item">Sequence Builder</span>'
            breadcrumb_html += '<span class="breadcrumb-separator">›</span>'
            breadcrumb_html += f'<span class="breadcrumb-item active">{pages[current_page]}</span>'
        elif current_page == "sequence":
            breadcrumb_html += '<span class="breadcrumb-item">Research Input</span>'
            breadcrumb_html += '<span class="breadcrumb-separator">›</span>'
            breadcrumb_html += '<span class="breadcrumb-item">Hypothesis</span>'
            breadcrumb_html += '<span class="breadcrumb-separator">›</span>'
            breadcrumb_html += f'<span class="breadcrumb-item active">{pages[current_page]}</span>'
        elif current_page == "hypothesis":
            breadcrumb_html += '<span class="breadcrumb-item">Research Input</span>'
            breadcrumb_html += '<span class="breadcrumb-separator">›</span>'
            breadcrumb_html += f'<span class="breadcrumb-item active">{pages[current_page]}</span>'
    else:
        breadcrumb_html += f'<span class="breadcrumb-separator">›</span>'
        breadcrumb_html += f'<span class="breadcrumb-item active">{pages[current_page]}</span>'
    
    breadcrumb_html += '</div>'
    st.markdown(breadcrumb_html, unsafe_allow_html=True)


def render_step_indicator(current_page: str):
    """Render step indicator showing progress through the workflow."""
    steps = [
        {"num": 1, "label": "Research Input", "page": "input"},
        {"num": 2, "label": "Hypothesis", "page": "hypothesis"},
        {"num": 3, "label": "Sequence", "page": "sequence"},
        {"num": 4, "label": "AE Handoff", "page": "ae_handoff"}
    ]
    
    page_order = {"input": 0, "hypothesis": 1, "sequence": 2, "ae_handoff": 3}
    current_index = page_order.get(current_page, 0)
    
    indicator_html = '<div class="step-indicator">'
    for i, step in enumerate(steps):
        classes = "step-item"
        if i < current_index:
            classes += " completed"
        elif i == current_index:
            classes += " active"
        
        indicator_html += f'<div class="{classes}">'
        indicator_html += f'<div class="step-number">{step["num"]}</div>'
        indicator_html += f'<div class="step-label">{step["label"]}</div>'
        indicator_html += '</div>'
    
    indicator_html += '</div>'
    st.markdown(indicator_html, unsafe_allow_html=True)


def render_status_badges():
    """Render status badges for demo mode and API connection."""
    demo_mode = st.session_state.get("demo_mode", False)
    provider = st.session_state.get("ai_provider", "gemini")
    
    if provider == "openai":
        has_api_key = bool(_get_openai_key())
    else:
        has_api_key = bool(_get_gemini_key())
    
    badges_html = '<div style="margin-bottom: 1rem;">'
    
    if demo_mode:
        badges_html += '<span class="status-badge badge-demo">🎭 Demo Mode</span>'
    else:
        provider_name = "OpenAI" if provider == "openai" else "Gemini"
        badges_html += f'<span class="status-badge badge-ai">🤖 {provider_name} Mode</span>'
        
        if has_api_key:
            badges_html += '<span class="status-badge badge-connected">✓ Connected</span>'
        else:
            badges_html += '<span class="status-badge badge-disconnected">⚠ No API Key</span>'
    
    badges_html += '</div>'
    st.markdown(badges_html, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with navigation and settings."""
    with st.sidebar:
        st.markdown("### About")
        st.markdown("Generate Cursor-specific outbound hypotheses and sequences from your research.")
        
        # Status badges
        render_status_badges()
        
        st.markdown("---")
        st.markdown("### Navigation")
        
        if st.button("1. Research Input", use_container_width=True):
            st.session_state.page = "input"
            st.rerun()
        if st.button("2. Hypothesis", use_container_width=True):
            st.session_state.page = "hypothesis"
            st.rerun()
        if st.button("3. Sequence Builder", use_container_width=True):
            st.session_state.page = "sequence"
            st.rerun()
        if st.button("4. AE Handoff", use_container_width=True):
            st.session_state.page = "ae_handoff"
            st.rerun()
        
        st.markdown("---")
        st.markdown("### Settings")
        
        # Demo mode toggle
        demo_mode = st.checkbox(
            "Demo Mode (No API Required)",
            value=st.session_state.get("demo_mode", False),
            help="Generate sample outputs without API calls. Perfect for testing!"
        )
        st.session_state.demo_mode = demo_mode
        
        if demo_mode:
            st.info("💡 Demo mode enabled - using sample outputs")
        else:
            # AI Provider selection
            provider_options = ["openai"]
            if GEMINI_AVAILABLE:
                provider_options.append("gemini")
            
            current_provider = st.session_state.get("ai_provider", "gemini")
            # If Gemini not available and user had it selected, default to OpenAI
            if current_provider == "gemini" and not GEMINI_AVAILABLE:
                current_provider = "openai"
                st.session_state.ai_provider = "openai"
            
            provider = st.radio(
                "AI Provider",
                provider_options,
                index=1 if (current_provider == "gemini" and "gemini" in provider_options) else 0,
                format_func=lambda x: "OpenAI (GPT-4o)" if x == "openai" else "Google Gemini (Free Tier)",
                help="Gemini free tier: 1,000 requests/day, 5-15 RPM. No credit card required!" if GEMINI_AVAILABLE else "Install google-generativeai package to use Gemini"
            )
            st.session_state.ai_provider = provider
            
            if not GEMINI_AVAILABLE and provider == "gemini":
                st.error("⚠️ Gemini package not installed. Run: pip3 install google-generativeai")
            
            # API Key inputs
            if provider == "openai":
                openai_key = _get_openai_key()
                if not openai_key:
                    api_key = st.text_input(
                        "OpenAI API Key",
                        type="password",
                        value=st.session_state.get("openai_api_key", ""),
                        help="Enter your OpenAI API key (get one at platform.openai.com)",
                        key="openai_key_input"
                    )
                    if api_key:
                        st.session_state.openai_api_key = api_key
                        st.success("✅ OpenAI API key set!")
                        if st.button("💾 Save key for next time", key="save_openai_key"):
                            _sf = Path(__file__).parent / "local_secrets.env"
                            try:
                                _lines = _sf.read_text().splitlines() if _sf.exists() else []
                                _lines = [l for l in _lines if l.strip() and not l.startswith("OPENAI_API_KEY=")]
                                _lines.insert(0, f"OPENAI_API_KEY={api_key}")
                                _sf.write_text("\n".join(_lines) + "\n")
                                st.success("✅ Key saved. Restart the app to load it automatically.")
                            except Exception as e:
                                st.warning(f"Could not save: {e}")
                else:
                    st.success("✅ OpenAI API key loaded from environment")
                    if st.button("💾 Save key for next time", key="save_openai_key"):
                        _sf = Path(__file__).parent / "local_secrets.env"
                        try:
                            _lines = _sf.read_text().splitlines() if _sf.exists() else []
                            _lines = [l for l in _lines if l.strip() and not l.startswith("OPENAI_API_KEY=")]
                            _lines.insert(0, f"OPENAI_API_KEY={openai_key}")
                            _sf.write_text("\n".join(_lines) + "\n")
                            st.success("✅ Key saved to local_secrets.env.")
                        except Exception as e:
                            st.warning(f"Could not save: {e}")
            else:  # Gemini
                gemini_key = _get_gemini_key()
                if not gemini_key:
                    api_key = st.text_input(
                        "Gemini API Key",
                        type="password",
                        value=st.session_state.get("gemini_api_key", ""),
                        help="Get free API key at aistudio.google.com/app/apikey (no credit card required!)",
                        key="gemini_key_input"
                    )
                    if api_key:
                        st.session_state.gemini_api_key = api_key
                        st.success("✅ Gemini API key set!")
                        if st.button("💾 Save key for next time", key="save_gemini_key"):
                            _sf = Path(__file__).parent / "local_secrets.env"
                            try:
                                _lines = _sf.read_text().splitlines() if _sf.exists() else []
                                _lines = [l for l in _lines if l.strip() and not l.startswith("GEMINI_API_KEY=")]
                                _lines.insert(0, f"GEMINI_API_KEY={api_key}")
                                _sf.write_text("\n".join(_lines) + "\n")
                                st.success("✅ Key saved. Restart the app to load it automatically.")
                            except Exception as e:
                                st.warning(f"Could not save: {e}")
                else:
                    st.success("✅ Gemini API key loaded from environment")
                    if st.button("💾 Save key for next time", key="save_gemini_key"):
                        _sf = Path(__file__).parent / "local_secrets.env"
                        try:
                            _lines = _sf.read_text().splitlines() if _sf.exists() else []
                            _lines = [l for l in _lines if l.strip() and not l.startswith("GEMINI_API_KEY=")]
                            _lines.insert(0, f"GEMINI_API_KEY={gemini_key}")
                            _sf.write_text("\n".join(_lines) + "\n")
                            st.success("✅ Key saved to local_secrets.env.")
                        except Exception as e:
                            st.warning(f"Could not save: {e}")
                
                st.info("💡 **Gemini Free Tier**: 1,000 requests/day, 5-15 RPM. Great for personal projects!")
                
                # Debug: Show available models
                if st.button("🔍 List Available Models", help="Check which Gemini models are available with your API key"):
                    with st.spinner("Checking available models..."):
                        models = list_available_gemini_models()
                        if models:
                            st.success(f"**Available models:** {', '.join(models)}")
                        else:
                            st.warning("Could not retrieve model list. Check your API key.")
        
        # Reset button
        st.markdown("---")
        if st.button("🔄 Reset All", use_container_width=True, help="Clear all data and return to research input"):
            # Preserve API keys and settings
            preserved_openai_key = st.session_state.get("openai_api_key")
            preserved_gemini_key = st.session_state.get("gemini_api_key")
            preserved_provider = st.session_state.get("ai_provider")
            preserved_demo_mode = st.session_state.get("demo_mode")
            
            for key in ['research_data', 'hypothesis', 'personas', 'selected_persona', 'sequence', 'prospect_info', 'csv_data', 'ae_handoff']:
                if key in st.session_state:
                    st.session_state[key] = {} if key in ['research_data', 'prospect_info'] else None if key in ['hypothesis', 'selected_persona', 'sequence', 'csv_data', 'ae_handoff'] else []
            
            # Restore preserved values
            if preserved_openai_key:
                st.session_state.openai_api_key = preserved_openai_key
            if preserved_gemini_key:
                st.session_state.gemini_api_key = preserved_gemini_key
            if preserved_provider:
                st.session_state.ai_provider = preserved_provider
            if preserved_demo_mode is not None:
                st.session_state.demo_mode = preserved_demo_mode
            
            st.session_state.page = "input"
            st.rerun()


def render_input_page():
    """Screen 1: Research Input"""
    st.title("🎯 Outbound Engine")
    
    # Breadcrumb and step indicator
    render_breadcrumb("input")
    render_step_indicator("input")
    
    # Refresh button at the top
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.markdown("### Research Input")
        st.markdown("Paste your research below to generate a Cursor-specific outbound hypothesis.")
    with col_refresh:
        if st.button("🔄 Refresh / Start Over", use_container_width=True, help="Clear all data and start fresh"):
            # Preserve API keys and settings
            preserved_openai_key = st.session_state.get("openai_api_key")
            preserved_gemini_key = st.session_state.get("gemini_api_key")
            preserved_provider = st.session_state.get("ai_provider")
            preserved_demo_mode = st.session_state.get("demo_mode")
            
            # Clear all session state
            for key in ['research_data', 'hypothesis', 'personas', 'selected_persona', 'sequence', 'sequences', 'selected_lanes', 'current_sequence_lane_id', 'prospect_info', 'csv_data', 'ae_handoff']:
                if key in st.session_state:
                    st.session_state[key] = {} if key in ['research_data', 'prospect_info', 'sequences'] else None if key in ['hypothesis', 'selected_persona', 'sequence', 'csv_data', 'ae_handoff', 'current_sequence_lane_id'] else [] if key in ['personas', 'selected_lanes'] else None
            
            # Restore preserved values
            if preserved_openai_key:
                st.session_state.openai_api_key = preserved_openai_key
            if preserved_gemini_key:
                st.session_state.gemini_api_key = preserved_gemini_key
            if preserved_provider:
                st.session_state.ai_provider = preserved_provider
            if preserved_demo_mode is not None:
                st.session_state.demo_mode = preserved_demo_mode
            
            st.session_state.page = "input"
            st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        company_info = st.text_area(
            "Company Overview",
            placeholder="Paste company info from website, Crunchbase, etc.\n\nInclude: company name, size, industry, funding, tech stack, recent news...",
            height=200,
            value=st.session_state.research_data.get("company_info", "")
        )
        
        job_postings = st.text_area(
            "Relevant Job Postings",
            placeholder="Paste as many relevant job postings as you have (3–5+ improves hypothesis quality).\n\nLook for: DevEx, Platform Engineering, Developer Productivity roles...",
            height=200,
            value=st.session_state.research_data.get("job_postings", "")
        )
    
    with col2:
        linkedin_profiles = st.text_area(
            "Target Persona LinkedIn Profiles",
            placeholder="Paste as many target persona profiles as you have (3–5+ improves hypothesis and sequences).\n\nInclude: name, title, background, recent posts...",
            height=200,
            value=st.session_state.research_data.get("linkedin_profiles", "")
        )
        
        news_signals = st.text_area(
            "Recent News/Signals",
            placeholder="Paste relevant headlines or summaries\n\nLook for: funding rounds, hiring surges, tech blog posts, conference talks...",
            height=200,
            value=st.session_state.research_data.get("news_signals", "")
        )
    
    st.markdown("#### Optional: Current customers to reference")
    reference_customers = st.text_area(
        "Current customers / references (similar accounts)",
        placeholder="Paste a short list of current customers you can reference (similar to this account).\n\nWe'll weave 1–2 references into the sequence (e.g. 'Teams at [X] have seen...'). Not required.",
        height=100,
        value=st.session_state.research_data.get("reference_customers", ""),
        key="research_reference_customers"
    )
    
    # Check if API key is configured or demo mode is enabled
    demo_mode = st.session_state.get("demo_mode", False)
    provider = get_ai_provider()
    if provider == "openai":
        has_api_key = bool(_get_openai_key())
    else:
        has_api_key = bool(_get_gemini_key())
    can_generate = demo_mode or has_api_key
    
    if not can_generate:
        provider_name = "OpenAI" if provider == "openai" else "Gemini"
        st.warning(f"💡 Enable 'Demo Mode' in the sidebar to test without an API key, or add your {provider_name} API key.")
    
    if st.button("Generate Hypothesis", type="primary", use_container_width=True, disabled=not can_generate):
        # Validate input
        if not any([company_info, job_postings, linkedin_profiles, news_signals]):
            st.error("Please provide at least some research data.")
            return
        
        # Store research data
        st.session_state.research_data = {
            "company_info": company_info,
            "job_postings": job_postings,
            "linkedin_profiles": linkedin_profiles,
            "news_signals": news_signals,
            "reference_customers": reference_customers.strip() if reference_customers else ""
        }
        
        # Generate hypothesis
        demo_mode = st.session_state.get("demo_mode", False)
        with st.spinner("Analyzing research and generating hypothesis..." if not demo_mode else "Generating sample hypothesis..."):
            hypothesis = generate_hypothesis(st.session_state.research_data, use_demo=demo_mode)
            st.session_state.hypothesis = hypothesis
            
            # Extract personas
            personas = extract_personas_from_hypothesis(hypothesis)
            st.session_state.personas = personas
        
        st.session_state.page = "hypothesis"
        st.rerun()


def render_hypothesis_page():
    """Screen 2: Hypothesis Output"""
    st.title("🎯 Outbound Engine")
    
    # Breadcrumb and step indicator
    render_breadcrumb("hypothesis")
    render_step_indicator("hypothesis")
    
    # Refresh button at the top
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.markdown("### Outbound Hypothesis")
    with col_refresh:
        if st.button("🔄 Refresh / Start Over", use_container_width=True, help="Clear all data and start fresh"):
            # Preserve API keys and settings
            preserved_openai_key = st.session_state.get("openai_api_key")
            preserved_gemini_key = st.session_state.get("gemini_api_key")
            preserved_provider = st.session_state.get("ai_provider")
            preserved_demo_mode = st.session_state.get("demo_mode")
            
            # Clear all session state
            for key in ['research_data', 'hypothesis', 'personas', 'selected_persona', 'sequence', 'sequences', 'selected_lanes', 'current_sequence_lane_id', 'prospect_info', 'csv_data', 'ae_handoff']:
                if key in st.session_state:
                    st.session_state[key] = {} if key in ['research_data', 'prospect_info', 'sequences'] else None if key in ['hypothesis', 'selected_persona', 'sequence', 'csv_data', 'ae_handoff', 'current_sequence_lane_id'] else [] if key in ['personas', 'selected_lanes'] else None
            
            # Restore preserved values
            if preserved_openai_key:
                st.session_state.openai_api_key = preserved_openai_key
            if preserved_gemini_key:
                st.session_state.gemini_api_key = preserved_gemini_key
            if preserved_provider:
                st.session_state.ai_provider = preserved_provider
            if preserved_demo_mode is not None:
                st.session_state.demo_mode = preserved_demo_mode
            
            st.session_state.page = "input"
            st.rerun()
    
    if not st.session_state.research_data:
        st.warning("No research data found. Please go back and input your research.")
        if st.button("← Back to Input"):
            st.session_state.page = "input"
            st.rerun()
        return
    
    # Show the hypothesis
    if st.session_state.hypothesis:
        st.markdown(st.session_state.hypothesis)
    else:
        # Generate if not yet done
        demo_mode = st.session_state.get("demo_mode", False)
        with st.spinner("Generating hypothesis..." if not demo_mode else "Generating sample hypothesis..."):
            hypothesis = generate_hypothesis(st.session_state.research_data, use_demo=demo_mode)
            st.session_state.hypothesis = hypothesis
            personas = extract_personas_from_hypothesis(hypothesis)
            st.session_state.personas = personas
            st.rerun()
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← Back to Input"):
            st.session_state.page = "input"
            st.rerun()
    
    with col2:
        if st.button("Regenerate", use_container_width=True):
            demo_mode = st.session_state.get("demo_mode", False)
            with st.spinner("Regenerating hypothesis..." if not demo_mode else "Regenerating sample hypothesis..."):
                hypothesis = generate_hypothesis(st.session_state.research_data, use_demo=demo_mode)
                st.session_state.hypothesis = hypothesis
                personas = extract_personas_from_hypothesis(hypothesis)
                st.session_state.personas = personas
                st.rerun()
    
    with col3:
        if st.button("Build Sequence →", type="primary"):
            st.session_state.page = "sequence"
            st.rerun()


def render_sequence_page():
    """Screen 3: Sequence Builder"""
    st.title("🎯 Outbound Engine")
    
    # Breadcrumb and step indicator
    render_breadcrumb("sequence")
    render_step_indicator("sequence")
    
    # Refresh button at the top
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.markdown("### Sequence Builder")
    with col_refresh:
        if st.button("🔄 Refresh / Start Over", use_container_width=True, help="Clear all data and start fresh"):
            # Preserve API keys and settings
            preserved_openai_key = st.session_state.get("openai_api_key")
            preserved_gemini_key = st.session_state.get("gemini_api_key")
            preserved_provider = st.session_state.get("ai_provider")
            preserved_demo_mode = st.session_state.get("demo_mode")
            
            # Clear all session state
            for key in ['research_data', 'hypothesis', 'personas', 'selected_persona', 'sequence', 'sequences', 'selected_lanes', 'current_sequence_lane_id', 'prospect_info', 'csv_data', 'ae_handoff']:
                if key in st.session_state:
                    st.session_state[key] = {} if key in ['research_data', 'prospect_info', 'sequences'] else None if key in ['hypothesis', 'selected_persona', 'sequence', 'csv_data', 'ae_handoff', 'current_sequence_lane_id'] else [] if key in ['personas', 'selected_lanes'] else None
            
            # Restore preserved values
            if preserved_openai_key:
                st.session_state.openai_api_key = preserved_openai_key
            if preserved_gemini_key:
                st.session_state.gemini_api_key = preserved_gemini_key
            if preserved_provider:
                st.session_state.ai_provider = preserved_provider
            if preserved_demo_mode is not None:
                st.session_state.demo_mode = preserved_demo_mode
            
            st.session_state.page = "input"
            st.rerun()
    
    if not st.session_state.hypothesis:
        st.warning("No hypothesis found. Please generate a hypothesis first.")
        if st.button("← Back to Hypothesis"):
            st.session_state.page = "hypothesis"
            st.rerun()
        return
    
    # Load persona lanes
    persona_lanes = load_persona_lanes()
    if not persona_lanes:
        st.warning("No persona lanes found. Add **kb/persona_lanes.md** with your persona buckets (see kb/README).")
    
    # Persona lane selection (1–3 scalable sequences)
    st.markdown("#### Persona Lanes")
    st.markdown("Select 1–3 persona lanes to generate scalable sequences you can use across many prospects in each bucket.")
    
    lane_options = [f"{lane['id']}. {lane['name']}" for lane in persona_lanes]
    lane_labels_to_lane = {f"{lane['id']}. {lane['name']}": lane for lane in persona_lanes}
    
    # Use key= so Streamlit tracks selection reliably (avoids buggy re-selects)
    if "persona_lane_multiselect" not in st.session_state:
        st.session_state.persona_lane_multiselect = lane_options[:1] if lane_options else []
    selected_labels = st.multiselect(
        "Choose persona lanes (1–3)",
        options=lane_options,
        max_selections=3,
        key="persona_lane_multiselect",
        help="Pick the audience buckets you want sequences for. Each gets its own hook and Cursor play."
    )
    st.session_state.selected_lanes = list(st.session_state.get("persona_lane_multiselect", selected_labels))
    
    # Optional example prospect (for draft personalization)
    st.markdown("#### Example prospect (optional)")
    st.markdown("Add one prospect to personalize the draft; otherwise sequences use placeholders like [First Name] and [Company] so you can scale.")
    
    col1, col2 = st.columns(2)
    with col1:
        first_name = st.text_input("First Name", value=st.session_state.prospect_info.get("first_name", ""), placeholder="John")
        last_name = st.text_input("Last Name", value=st.session_state.prospect_info.get("last_name", ""), placeholder="Smith")
        email = st.text_input("Email", value=st.session_state.prospect_info.get("email", ""), placeholder="john.smith@company.com")
    with col2:
        company = st.text_input("Company", value=st.session_state.prospect_info.get("company", ""), placeholder="Acme Corp")
        title = st.text_input("Job Title (optional)", value=st.session_state.prospect_info.get("title", ""), placeholder="VP Engineering")
    
    st.session_state.prospect_info = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "company": company,
        "title": title
    }
    
    st.markdown("---")
    
    # Generate sequences button
    demo_mode = st.session_state.get("demo_mode", False)
    provider = get_ai_provider()
    if provider == "openai":
        has_api_key = bool(_get_openai_key())
    else:
        has_api_key = bool(_get_gemini_key())
    can_generate = demo_mode or has_api_key
    
    if st.button("Generate sequences", type="primary", use_container_width=True, disabled=not can_generate):
        if not selected_labels:
            st.error("Please select at least one persona lane.")
        else:
            lanes_to_gen = [lane_labels_to_lane[label] for label in selected_labels if label in lane_labels_to_lane]
            if not lanes_to_gen:
                st.error("Could not resolve selected lanes.")
            else:
                st.session_state.sequences = {}
                for idx, lane in enumerate(lanes_to_gen):
                    with st.spinner(f"Generating sequence {idx + 1}/{len(lanes_to_gen)}: {lane['name']}..." if not demo_mode else f"Sample sequence {idx + 1}/{len(lanes_to_gen)}: {lane['name']}..."):
                        content = generate_sequence(
                            lane,
                            st.session_state.hypothesis,
                            st.session_state.prospect_info,
                            use_demo=demo_mode,
                            reference_customers=st.session_state.research_data.get("reference_customers", "")
                        )
                        st.session_state.sequences[lane["id"]] = {"name": lane["name"], "content": content}
                st.session_state.current_sequence_lane_id = lanes_to_gen[0]["id"]
                st.session_state.csv_data = None
                st.rerun()
    
    # Display generated sequences (selector + one at a time)
    if st.session_state.sequences:
        st.markdown("---")
        lane_ids = list(st.session_state.sequences.keys())
        current_id = st.session_state.current_sequence_lane_id or lane_ids[0]
        if current_id not in lane_ids:
            current_id = lane_ids[0]
            st.session_state.current_sequence_lane_id = current_id
        
        display_names = [st.session_state.sequences[lid]["name"] for lid in lane_ids]
        selected_index = lane_ids.index(current_id)
        chosen = st.selectbox("View sequence", options=display_names, index=selected_index)
        st.session_state.current_sequence_lane_id = lane_ids[display_names.index(chosen)]
        current_content = st.session_state.sequences[st.session_state.current_sequence_lane_id]["content"]
        
        st.markdown(f"#### {chosen}")
        st.markdown(current_content)
        
        # Export section (for current sequence)
        st.markdown("---")
        st.markdown("#### Export to Outreach.io")
        export_prospect = st.session_state.prospect_info
        if not export_prospect.get("first_name") or not export_prospect.get("company"):
            export_prospect = {
                "first_name": "[First Name]",
                "last_name": "[Last Name]",
                "email": "[Email]",
                "company": "[Company]",
                "title": "[Title]"
            }
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate CSV Export", use_container_width=True, disabled=demo_mode):
                with st.spinner("Formatting sequence for export..."):
                    df = parse_sequence_to_csv(current_content, export_prospect)
                    if not df.empty:
                        st.session_state.csv_data = df.to_csv(index=False)
                        step_count = len(df)
                        max_step = int(df['step_number'].max()) if 'step_number' in df.columns and not df['step_number'].isna().all() else step_count
                        st.success(f"✅ CSV generated with {step_count} step(s) (up to step {max_step})!")
                        st.dataframe(df, use_container_width=True)
            elif demo_mode:
                st.info("💡 CSV export requires API access. Enable AI mode in sidebar to export.")
        with col2:
            if st.session_state.get("csv_data"):
                safe_name = (export_prospect.get("company") or chosen).replace(" ", "_").replace("[", "").replace("]", "").lower()
                st.download_button(
                    "Download CSV",
                    data=st.session_state.csv_data,
                    file_name=f"outreach_sequence_{safe_name}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Back to Hypothesis"):
            st.session_state.page = "hypothesis"
            st.rerun()
    with col2:
        if st.session_state.sequences:
            if st.button("Generate different lanes", use_container_width=True):
                st.session_state.sequences = {}
                st.session_state.selected_lanes = []
                st.session_state.current_sequence_lane_id = None
                st.session_state.csv_data = None
                if "persona_lane_multiselect" in st.session_state:
                    st.session_state.persona_lane_multiselect = []
                st.rerun()
    with col3:
        if st.button("AE Handoff →", type="primary", use_container_width=True):
            st.session_state.page = "ae_handoff"
            st.rerun()


def render_ae_handoff_page():
    """Screen 4: AE Handoff - handoff note + first call agenda from hypothesis."""
    st.title("🎯 Outbound Engine")
    
    render_breadcrumb("ae_handoff")
    render_step_indicator("ae_handoff")
    
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.markdown("### AE Handoff")
        st.markdown("Generate a handoff note and first call agenda for the Account Executive from the hypothesis.")
    with col_refresh:
        if st.button("🔄 Refresh / Start Over", use_container_width=True, help="Clear all data and start fresh"):
            preserved_openai_key = st.session_state.get("openai_api_key")
            preserved_gemini_key = st.session_state.get("gemini_api_key")
            preserved_provider = st.session_state.get("ai_provider")
            preserved_demo_mode = st.session_state.get("demo_mode")
            for key in ['research_data', 'hypothesis', 'personas', 'selected_persona', 'sequence', 'sequences', 'selected_lanes', 'current_sequence_lane_id', 'prospect_info', 'csv_data', 'ae_handoff']:
                if key in st.session_state:
                    st.session_state[key] = {} if key in ['research_data', 'prospect_info', 'sequences'] else None if key in ['hypothesis', 'selected_persona', 'sequence', 'csv_data', 'ae_handoff', 'current_sequence_lane_id'] else [] if key in ['personas', 'selected_lanes'] else None
            if preserved_openai_key:
                st.session_state.openai_api_key = preserved_openai_key
            if preserved_gemini_key:
                st.session_state.gemini_api_key = preserved_gemini_key
            if preserved_provider:
                st.session_state.ai_provider = preserved_provider
            if preserved_demo_mode is not None:
                st.session_state.demo_mode = preserved_demo_mode
            st.session_state.page = "input"
            st.rerun()
    
    if not st.session_state.hypothesis:
        st.warning("No hypothesis found. Generate a hypothesis first (Research Input → Generate Hypothesis).")
        if st.button("← Back to Hypothesis"):
            st.session_state.page = "hypothesis"
            st.rerun()
        return
    
    demo_mode = st.session_state.get("demo_mode", False)
    provider = get_ai_provider()
    has_api_key = bool(_get_openai_key()) if provider == "openai" else bool(_get_gemini_key())
    can_generate = has_api_key and not demo_mode
    
    if st.button("Generate AE Handoff", type="primary", use_container_width=True, disabled=not can_generate):
        with st.spinner("Generating handoff note and first call agenda..."):
            result = generate_ae_handoff(st.session_state.hypothesis)
            st.session_state.ae_handoff = result
            st.rerun()
    
    if demo_mode and not has_api_key:
        st.info("💡 Enable AI mode and add an API key in the sidebar to generate the AE handoff.")
    
    if st.session_state.ae_handoff:
        st.markdown("---")
        st.markdown("#### Generated AE Handoff")
        st.markdown(st.session_state.ae_handoff)
    
    st.markdown("---")
    if st.button("← Back to Sequence Builder"):
        st.session_state.page = "sequence"
        st.rerun()


def main():
    """Main application entry point."""
    render_sidebar()
    
    # Render current page
    if st.session_state.page == "input":
        render_input_page()
    elif st.session_state.page == "hypothesis":
        render_hypothesis_page()
    elif st.session_state.page == "sequence":
        render_sequence_page()
    elif st.session_state.page == "ae_handoff":
        render_ae_handoff_page()


if __name__ == "__main__":
    main()

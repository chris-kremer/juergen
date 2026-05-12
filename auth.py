"""
Authentication system for the portfolio application
"""

import streamlit as st
from typing import Optional, Dict
from config import USERS
from translations import get_language, get_text
from login_tracker import login_tracker
from security import get_configured_password_hash, verify_password
import time


MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60

class AuthSystem:
    def __init__(self):
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'current_user' not in st.session_state:
            st.session_state.current_user = None
        if 'failed_login_attempts' not in st.session_state:
            st.session_state.failed_login_attempts = {}

    def _find_user(self, username: str) -> Optional[Dict]:
        normalized_username = username.strip().lower()
        return next((user for user in USERS if user['username'] == normalized_username), None)

    def _is_locked_out(self, username: str) -> bool:
        attempt_state = st.session_state.failed_login_attempts.get(username, {})
        locked_until = attempt_state.get("locked_until", 0)
        return locked_until > time.time()

    def _record_failed_attempt(self, username: str):
        attempt_state = st.session_state.failed_login_attempts.get(username, {"count": 0})
        count = attempt_state.get("count", 0) + 1
        attempt_state["count"] = count

        if count >= MAX_FAILED_ATTEMPTS:
            attempt_state["locked_until"] = time.time() + LOCKOUT_SECONDS

        st.session_state.failed_login_attempts[username] = attempt_state

    def _clear_failed_attempts(self, username: str):
        st.session_state.failed_login_attempts.pop(username, None)
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate user with username and password
        Returns True if authentication successful, False otherwise
        """
        normalized_username = username.strip().lower()

        if self._is_locked_out(normalized_username):
            return False

        user = self._find_user(normalized_username)
        password_hash = get_configured_password_hash(normalized_username)

        if user and password_hash and verify_password(password, password_hash):
            st.session_state.authenticated = True
            # Keep sensitive auth material out of the session.
            st.session_state.current_user = user.copy()
            self._clear_failed_attempts(normalized_username)
            login_tracker.log_login(normalized_username)
            return True

        self._record_failed_attempt(normalized_username)
        return False
    
    def logout(self):
        """Logout current user"""
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self) -> Optional[Dict]:
        """Get current authenticated user"""
        return st.session_state.get('current_user', None)
    
    def show_login_form(self):
        """Display login form"""
        st.title(get_text('portfolio_login'))
        st.markdown("---")
        
        # Center the login form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown(f"### {get_text('please_log_in')}")
            if not any(get_configured_password_hash(user["username"]) for user in USERS):
                st.warning("Authentication is not configured. Add password hashes to Streamlit secrets.")
            
            with st.form("login_form"):
                username = st.text_input(get_text('username'), placeholder=get_text('enter_username'))
                password = st.text_input(get_text('password'), type="password", placeholder=get_text('enter_password'))
                submit_button = st.form_submit_button(get_text('login'), use_container_width=True)
                
                if submit_button:
                    if username and password:
                        if self.authenticate(username, password):
                            lang = get_language(username)
                            st.success(get_text('login_successful', lang))
                            st.rerun()
                        else:
                            st.error(get_text('invalid_credentials'))
                    else:
                        st.warning(get_text('enter_both'))
        

    
    def show_user_info(self):
        """Display current user info in sidebar"""
        user = self.get_current_user()
        if user:
            lang = get_language(user['username'])
            with st.sidebar:
                st.markdown(f"### {get_text('welcome', lang, user['username'].title())}")
                
                if st.button(get_text('logout', lang), use_container_width=True):
                    self.logout()

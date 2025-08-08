"""
Authentication system for the portfolio application
"""

import streamlit as st
from typing import Optional, Dict
from config import USERS
from translations import get_language, get_text

class AuthSystem:
    def __init__(self):
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'current_user' not in st.session_state:
            st.session_state.current_user = None
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate user with username and password
        Returns True if authentication successful, False otherwise
        """
        for user in USERS:
            if user['username'] == username and user['password'] == password:
                st.session_state.authenticated = True
                st.session_state.current_user = user
                return True
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
                st.markdown(f"**{get_text('portfolio_share', lang)}:** {user['portfolio_percentage']*100:.2f}%")
                
                if st.button(get_text('logout', lang), use_container_width=True):
                    self.logout()

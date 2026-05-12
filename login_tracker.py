"""
Login tracking system using Google Sheets
"""

import streamlit as st
from datetime import datetime
import sys

class LoginTracker:
    def __init__(self):
        self.enabled = False
        self.sheet = None
        self._initialized = False

    def _initialize(self):
        """Initialize Google Sheets connection (lazy initialization)"""
        if self._initialized:
            return

        self._initialized = True

        try:
            # Check if Google Sheets credentials are available
            if 'gsheet_credentials' in st.secrets:
                import gspread
                from google.oauth2.service_account import Credentials

                # Define the scope
                scope = [
                    "https://www.googleapis.com/auth/spreadsheets",
                ]

                # Create credentials from secrets
                credentials = Credentials.from_service_account_info(
                    st.secrets["gsheet_credentials"],
                    scopes=scope
                )

                # Authorize and get the sheet
                client = gspread.authorize(credentials)

                # Open the spreadsheet (you'll need to create this and share it with the service account)
                # Try to get sheet URL from root level first, then from gsheet_credentials
                sheet_url = st.secrets.get("login_sheet_url", "")
                if not sheet_url and "login_sheet_url" in st.secrets.get("gsheet_credentials", {}):
                    sheet_url = st.secrets["gsheet_credentials"]["login_sheet_url"]
                if sheet_url:
                    self.sheet = client.open_by_url(sheet_url).sheet1
                    self.enabled = True

        except Exception as e:
            # Silently fail if credentials not configured
            # This allows the app to run without tracking if not set up
            print(f"Login tracking not configured: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc()
            self.enabled = False

    def log_login(self, username: str):
        """Log a successful login"""
        # Initialize on first use
        self._initialize()

        if not self.enabled:
            return

        try:
            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Get user agent (browser info)
            user_agent = "Unknown"
            try:
                import streamlit.web.server.server as server
                session_info = server.Server.get_current()._session_info_by_id
                if session_info:
                    # Try to get session info (this is approximate)
                    user_agent = "Streamlit Session"
            except:
                pass

            # Append row to sheet: [Timestamp, Username, User Agent]
            self.sheet.append_row([timestamp, username, user_agent])

        except Exception as e:
            # Log error but don't break the app
            print(f"Failed to log login: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc()

    def get_login_stats(self):
        """Get login statistics (for admin view)"""
        # Initialize on first use
        self._initialize()

        if not self.enabled:
            return None

        try:
            # Get all records
            records = self.sheet.get_all_records()
            return records
        except Exception as e:
            print(f"Failed to get login stats: {e}")
            return None

# Create a singleton instance
login_tracker = LoginTracker()

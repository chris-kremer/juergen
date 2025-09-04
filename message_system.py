"""
Message system for user notifications and updates
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz
from translations import get_language, get_text, format_currency_change

class MessageSystem:
    def __init__(self):
        self.messages_file = "user_messages.json"
        self.user_data_file = "user_data.json"
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Initialize message and user data files if they don't exist"""
        if not os.path.exists(self.messages_file):
            with open(self.messages_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.user_data_file):
            with open(self.user_data_file, 'w') as f:
                json.dump({}, f)
    
    def _load_messages(self) -> Dict:
        """Load user messages from file"""
        try:
            with open(self.messages_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_messages(self, messages: Dict):
        """Save user messages to file"""
        with open(self.messages_file, 'w') as f:
            json.dump(messages, f, indent=2)
    
    def _load_user_data(self) -> Dict:
        """Load user data from file"""
        try:
            with open(self.user_data_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_user_data(self, user_data: Dict):
        """Save user data to file"""
        with open(self.user_data_file, 'w') as f:
            json.dump(user_data, f, indent=2)
    
    def add_one_time_message(self, username: str, message: str, message_type: str = "info"):
        """Add a one-time message for a user"""
        messages = self._load_messages()
        
        if username not in messages:
            messages[username] = {"one_time": [], "dismissed": []}
        
        message_data = {
            "id": f"msg_{datetime.now().timestamp()}",
            "message": message,
            "type": message_type,
            "created": datetime.now().isoformat()
        }
        
        messages[username]["one_time"].append(message_data)
        self._save_messages(messages)
    
    def add_global_one_time_message(self, message: str, message_type: str = "info"):
        """Add a one-time message for all users"""
        from config import USERS
        
        for user in USERS:
            self.add_one_time_message(user["username"], message, message_type)
    
    def dismiss_message(self, username: str, message_id: str):
        """Dismiss a specific message for a user"""
        messages = self._load_messages()
        
        if username in messages:
            # Move from one_time to dismissed
            one_time_messages = messages[username].get("one_time", [])
            dismissed_messages = messages[username].get("dismissed", [])
            
            for i, msg in enumerate(one_time_messages):
                if msg["id"] == message_id:
                    dismissed_msg = one_time_messages.pop(i)
                    dismissed_messages.append(dismissed_msg)
                    break
            
            messages[username]["one_time"] = one_time_messages
            messages[username]["dismissed"] = dismissed_messages
            self._save_messages(messages)
    
    def update_last_login(self, username: str, portfolio_value: float):
        """Update user's last login time and portfolio value"""
        user_data = self._load_user_data()
        
        if username not in user_data:
            user_data[username] = {}
        
        # Store previous values
        user_data[username]["previous_login"] = user_data[username].get("last_login")
        user_data[username]["previous_portfolio_value"] = user_data[username].get("last_portfolio_value")
        
        # Update current values
        user_data[username]["last_login"] = datetime.now().isoformat()
        user_data[username]["last_portfolio_value"] = portfolio_value
        
        self._save_user_data(user_data)
    
    def get_value_change_message(self, username: str, current_value: float) -> Optional[Dict]:
        """Get portfolio value change message since last login"""
        user_data = self._load_user_data()
        lang = get_language(username)
        
        if username in user_data:
            previous_value = user_data[username].get("previous_portfolio_value")
            previous_login = user_data[username].get("previous_login")
            
            if previous_value is not None and previous_login is not None:
                change = current_value - previous_value
                change_pct = (change / previous_value * 100) if previous_value > 0 else 0
                
                # Parse previous login date
                try:
                    prev_login_dt = datetime.fromisoformat(previous_login)
                    days_ago = (datetime.now() - prev_login_dt).days
                    
                    if days_ago > 0:  # Only show if it's been at least a day
                        if change > 0:
                            message_type = "success"
                            emoji = "📈"
                        elif change < 0:
                            message_type = "error" 
                            emoji = "📉"
                        else:
                            message_type = "info"
                            emoji = "➡️"
                        
                        if lang == 'de':
                            if days_ago == 1:
                                time_text = "seit gestern"
                            else:
                                time_text = f"seit vor {days_ago} Tagen"
                            
                            message = f"{emoji} Ihr Portfolio hat sich um {format_currency_change(change, lang)} ({change_pct:+.1f}%) {time_text} verändert."
                        else:
                            if days_ago == 1:
                                time_text = "since yesterday"
                            else:
                                time_text = f"since {days_ago} days ago"
                                
                            message = f"{emoji} Your portfolio changed by {format_currency_change(change, lang)} ({change_pct:+.1f}%) {time_text}."
                        
                        return {
                            "message": message,
                            "type": message_type,
                            "is_value_change": True
                        }
                except:
                    pass
        
        return None
    
    def get_weekend_message(self, username: str) -> Optional[Dict]:
        """Get weekend trading message if it's weekend"""
        # Get current time in Eastern Time (NYSE timezone)
        try:
            et_tz = pytz.timezone('US/Eastern')
            now_et = datetime.now(et_tz)
        except:
            # Fallback to local time if timezone fails
            now_et = datetime.now()
        
        # For testing purposes, you can force weekend message by checking for test mode
        # Remove this after testing
        test_mode = False  # Set to False in production
        
        # Check if it's weekend (Saturday = 5, Sunday = 6) OR test mode
        if now_et.weekday() in [5, 6] or test_mode:  # Saturday or Sunday or test mode
            lang = get_language(username)
            
            if lang == 'de':
                message = "🏖️ Es ist Wochenende. Heute wird nicht gehandelt, aber hier sind die neuesten verfügbaren Daten:"
            else:
                message = "🏖️ It's the weekend. No trading today, but here's the latest available data:"
            
            return {
                "message": message,
                "type": "info",
                "is_weekend": True
            }
        
        return None
    
    def get_user_messages(self, username: str, current_portfolio_value: float) -> List[Dict]:
        """Only return the weekend message (suppress all others)."""
        weekend_msg = self.get_weekend_message(username)
        return [weekend_msg] if weekend_msg else []
    
    def show_messages(self, username: str, current_portfolio_value: float):
        """Display all pending messages for a user"""
        messages = self.get_user_messages(username, current_portfolio_value)
        
        if not messages:
            return
        
        # Display messages
        for msg in messages:
            message_text = msg["message"]
            message_type = msg["type"]
            
            if message_type == "success":
                st.success(message_text)
            elif message_type == "error":
                st.error(message_text)
            elif message_type == "warning":
                st.warning(message_text)
            else:
                st.info(message_text)
            
            # Add dismiss button for dismissible messages
            if msg.get("is_dismissible") and msg.get("id"):
                col1, col2 = st.columns([4, 1])
                with col2:
                    if st.button("✕", key=f"dismiss_{msg['id']}", help="Dismiss"):
                        self.dismiss_message(username, msg["id"])
                        st.rerun()
        
        # Update last login after showing messages
        self.update_last_login(username, current_portfolio_value)

# Global message system instance
message_system = MessageSystem()

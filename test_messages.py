"""
Test script to add sample messages for testing the message system
"""

from message_system import message_system

# Add some test messages
def add_test_messages():
    # Add a one-time message for all users
    message_system.add_global_one_time_message(
        "🎉 Welcome to the new Portfolio Overview! We've added message notifications to keep you informed.",
        "success"
    )
    
    # Add specific test messages
    message_system.add_one_time_message(
        "juergen", 
        "📊 Dein Portfolio-Dashboard wurde aktualisiert mit neuen Features!", 
        "info"
    )
    
    message_system.add_one_time_message(
        "kremer",
        "💡 Neue Funktion: Du erhältst jetzt Benachrichtigungen über Portfolio-Änderungen!",
        "info"
    )
    
    message_system.add_one_time_message(
        "christian",
        "🚀 New feature: You'll now receive notifications about portfolio changes!",
        "info"
    )
    
    print("Test messages added successfully!")

if __name__ == "__main__":
    add_test_messages()

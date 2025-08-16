"""
Test script to add sample messages for testing the message system
"""

from message_system import message_system

# Add some test messages (optional - uncomment what you want to test)
def add_test_messages():
    # Uncomment to add specific test messages (not recommended for production)
    # message_system.add_one_time_message(
    #     "foehr", 
    #     "Hey Christian & Sherry. Welcome to your stock overview!", 
    #     "info"
    # )
    
    # message_system.add_one_time_message(
    #     "kremer",
    #     "💡 Neue Funktion: Du erhältst jetzt Benachrichtigungen!",
    #     "info"
    # )
    
    # message_system.add_one_time_message(
    #     "christian",
    #     "🚀 New feature: You'll now receive notifications!",
    #     "info"
    # )

    print("No messages added (all commented out for production)")

if __name__ == "__main__":
    add_test_messages()

"""
Chat Interface Logic for Air India Chatbot
===========================================
Handles chat display, input processing, and conversation management.
"""

import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime


class ChatInterface:
    """Manages the chat interface and conversation flow"""

    def __init__(self):
        """Initialize chat interface"""
        self.initialize_chat_history()

    def initialize_chat_history(self):
        """Initialize chat history in session state"""
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": self._get_welcome_message()
                }
            ]

    def _get_welcome_message(self) -> str:
        """Get welcome message"""
        return (
            "**Namaste!** 👋 I'm **Maharaja**, your Air India virtual assistant. 🏆\n\n"
            "I can help you with:\n\n"
            "• **Flight Search** - Find Air India flights\n"
            "• **Policy Questions** - Check baggage rules and policies\n"
            "• **General Assistance** - Answer questions about Air India\n\n"
            "**Select a quick question or type your query:**"
        )

    def display_chat_area(self, title: str = "💬 Conversation"):
        """
        Display the main chat area

        Args:
            title: Title for the chat section
        """
        st.subheader(title)

        # Create container for chat messages
        with st.container():
            chat_container = st.container()
            with chat_container:
                # Import display_chat_history from components
                from .components import display_chat_history
                display_chat_history(st.session_state.messages)

    def add_user_message(self, message: str):
        """
        Add user message to chat history

        Args:
            message: User message content
        """
        if message and message.strip():
            st.session_state.messages.append({
                "role": "user",
                "content": message.strip(),
                "timestamp": datetime.now().isoformat()
            })

    def add_assistant_message(self, message: str):
        """
        Add assistant message to chat history

        Args:
            message: Assistant message content
        """
        if message and message.strip():
            st.session_state.messages.append({
                "role": "assistant",
                "content": message.strip(),
                "timestamp": datetime.now().isoformat(),
                "source": "chatbot"
            })

    def get_conversation_history(self, max_messages: int = 10) -> List[Dict]:
        """
        Get recent conversation history

        Args:
            max_messages: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        if "messages" not in st.session_state:
            return []

        # Return last N messages for context
        return st.session_state.messages[-max_messages:]

    def get_last_user_message(self) -> Optional[str]:
        """
        Get the last user message

        Returns:
            Last user message or None
        """
        if "messages" not in st.session_state:
            return None

        # Search from end to beginning
        for msg in reversed(st.session_state.messages):
            if msg["role"] == "user":
                return msg["content"]

        return None

    def get_last_assistant_message(self) -> Optional[str]:
        """
        Get the last assistant message

        Returns:
            Last assistant message or None
        """
        if "messages" not in st.session_state:
            return None

        # Search from end to beginning
        for msg in reversed(st.session_state.messages):
            if msg["role"] == "assistant":
                return msg["content"]

        return None

    def clear_chat_history(self):
        """Clear chat history and start new conversation"""
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm Maharaja, your Air India assistant. How can I help you today?"
            }
        ]

    def get_spinner_text(self, user_input: str) -> str:
        """
        Get appropriate spinner text based on user input

        Args:
            user_input: User's query

        Returns:
            Spinner text
        """
        user_input_lower = user_input.lower()

        if any(word in user_input_lower for word in ['flight', 'fly', 'book', 'del', 'bom', 'blr', 'maa']):
            return "✈️ Searching flight information..."

        elif any(word in user_input_lower for word in ['baggage', 'luggage', 'policy', 'checkin', 'cancel']):
            return "📚 Consulting Air India policies..."

        else:
            return "💭 Processing your query..."

    def process_quick_question(self, question: str, response_function) -> bool:
        """
        Process a quick question button click

        Args:
            question: The quick question
            response_function: Function to get response

        Returns:
            True if processed, False otherwise
        """
        if not question:
            return False

        # Add user message
        self.add_user_message(question)

        # Get response with spinner
        spinner_text = self.get_spinner_text(question)
        with st.spinner(spinner_text):
            response = response_function(question)

        # Add assistant response
        self.add_assistant_message(response)

        return True

    def process_text_input(self, user_input: str, send_button: bool, response_function) -> bool:
        """
        Process text input from user

        Args:
            user_input: User's text input
            send_button: Whether send button was pressed
            response_function: Function to get response

        Returns:
            True if processed, False otherwise
        """
        if not send_button or not user_input:
            return False

        # Add user message
        self.add_user_message(user_input)

        # Get response with spinner
        spinner_text = self.get_spinner_text(user_input)
        with st.spinner(spinner_text):
            response = response_function(user_input)

        # Add assistant response
        self.add_assistant_message(response)

        return True

    def get_statistics(self) -> Dict:
        """
        Get chat statistics

        Returns:
            Dictionary with statistics
        """
        if "messages" not in st.session_state:
            return {}

        messages = st.session_state.messages

        # Count messages by role
        user_count = sum(1 for msg in messages if msg["role"] == "user")
        assistant_count = sum(1 for msg in messages if msg["role"] == "assistant")

        # Calculate average message lengths
        user_lengths = [len(msg["content"]) for msg in messages if msg["role"] == "user"]
        assistant_lengths = [len(msg["content"]) for msg in messages if msg["role"] == "assistant"]

        avg_user_length = sum(user_lengths) / len(user_lengths) if user_lengths else 0
        avg_assistant_length = sum(assistant_lengths) / len(assistant_lengths) if assistant_lengths else 0

        return {
            "total_messages": len(messages),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "avg_user_length": round(avg_user_length, 1),
            "avg_assistant_length": round(avg_assistant_length, 1),
            "first_message_time": messages[0].get("timestamp", "N/A") if messages else "N/A",
            "last_message_time": messages[-1].get("timestamp", "N/A") if messages else "N/A"
        }


# Factory function
def create_chat_interface() -> ChatInterface:
    """
    Create a ChatInterface instance

    Returns:
        ChatInterface instance
    """
    return ChatInterface()


if __name__ == "__main__":
    # Test the chat interface
    import streamlit as st

    st.set_page_config(page_title="Chat Interface Test", page_icon="✈️")

    chat = create_chat_interface()

    st.title("Chat Interface Test")

    # Display chat
    chat.display_chat_area("Test Chat")

    # Test adding messages
    if st.button("Add Test Message"):
        chat.add_user_message("This is a test user message")
        chat.add_assistant_message("This is a test assistant response")
        st.rerun()

    # Show statistics
    if st.button("Show Statistics"):
        stats = chat.get_statistics()
        st.write(stats)

    # Clear chat
    if st.button("Clear Chat"):
        chat.clear_chat_history()
        st.rerun()
"""
UI Components for Air India Chatbot
====================================
Reusable Streamlit components for consistent UI.
"""

import streamlit as st
from datetime import datetime
import time


class UIConstants:
    """CSS constants and styling"""

    # CSS Styles
    MAIN_STYLES = """
    <style>
        .main-container { max-width: 900px; margin: 0 auto; }
        
        /* USER BUBBLE - Blue gradient with blue border */
        .chat-user { 
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
            padding: 14px 18px; 
            border-radius: 15px 15px 15px 5px; 
            margin: 12px 0; 
            border-left: 4px solid #1976d2; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            max-width: 80%; 
            margin-left: auto; 
        }
        
        /* BOT BUBBLE - Grey gradient with RED border */
        .chat-bot { 
            background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%); 
            padding: 14px 18px; 
            border-radius: 15px 15px 5px 15px; 
            margin: 12px 0; 
            border-left: 4px solid #d32f2f; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            max-width: 80%; 
            margin-right: auto; 
        }
        
        .quick-question-btn { 
            background: white; 
            border: 2px solid #d32f2f; 
            color: #d32f2f; 
            padding: 10px 16px; 
            margin: 6px 3px; 
            border-radius: 25px; 
            cursor: pointer; 
            font-weight: 500; 
            transition: all 0.3s ease; 
            text-align: center; 
            font-size: 14px; 
            white-space: nowrap; 
            overflow: hidden; 
            text-overflow: ellipsis; 
        }
        .quick-question-btn:hover { 
            background: #d32f2f; 
            color: white; 
            transform: translateY(-2px); 
            box-shadow: 0 4px 8px rgba(211, 47, 47, 0.2); 
        }
        
        .chat-container { 
            background: white; 
            border-radius: 10px; 
            padding: 20px; 
            margin: 20px 0; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
            max-height: 500px; 
            overflow-y: auto; 
        }
        
        .stTextInput > div > div > input { 
            border-radius: 25px; 
            padding: 12px 20px; 
            border: 2px solid #d32f2f; 
            font-size: 16px; 
        }
        
        .stButton > button { 
            border-radius: 25px; 
            padding: 12px 30px; 
            background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); 
            color: white; 
            font-weight: 600; 
            border: none; 
            transition: all 0.3s ease; 
            font-size: 16px; 
            height: 100%; 
        }
        .stButton > button:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 12px rgba(211, 47, 47, 0.3); 
            background: linear-gradient(135deg, #b71c1c 0%, #9a0007 100%); 
        }
        
        .main-header { 
            background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); 
            padding: 25px; 
            border-radius: 15px; 
            color: white; 
            text-align: center; 
            margin-bottom: 25px; 
            box-shadow: 0 4px 12px rgba(211, 47, 47, 0.2); 
        }
        
        [data-testid="stSidebar"] { 
            background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%); 
        }
        
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb { background: #d32f2f; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #b71c1c; }
        .stButton button:active { transform: scale(0.98); }
        
        /* DEBUG STYLES */
        .debug-info { 
            background: #f8f9fa; 
            border: 1px solid #dee2e6; 
            border-radius: 8px; 
            padding: 12px; 
            margin: 8px 0; 
            font-family: monospace; 
            font-size: 12px; 
            max-height: 200px; 
            overflow-y: auto; 
        }
        .debug-success { color: #28a745; font-weight: bold; }
        .debug-warning { color: #ffc107; font-weight: bold; }
        .debug-error { color: #dc3545; font-weight: bold; }
        .debug-time { color: #6c757d; }
        
        /* SIDEBAR STATUS STYLES */
        .status-item { 
            margin: 5px 0; 
            padding: 8px 12px; 
            border-radius: 8px; 
            background: #f8f9fa; 
            border-left: 4px solid; 
        }
        .status-success { border-left-color: #28a745; }
        .status-error { border-left-color: #dc3545; }
        .status-warning { border-left-color: #ffc107; }
        .status-info { border-left-color: #17a2b8; }
    </style>
    """

    # Quick questions
    QUICK_QUESTIONS = [
        "✈️ DEL to BOM flights tomorrow",
        "🧳 Baggage allowance for USA flights",
        "🎫 How to check-in online?",
        "🏆 Maharaja Club benefits",
        "💰 Flight cancellation policy",
        "💺 Seat selection process",
        "🍱 Vegetarian meal options",
        "🛄 Carry-on luggage size",
        "👶 Child ticket policy",
        "🌍 Flights to London",
        "⏰ Check-in closing time",
        "📱 Mobile app features"
    ]

    # System info
    SYSTEM_INFO = {
        "company": "Air India",
        "assistant_name": "Maharaja",
        "version": "Modular Architecture v1.0",
        "customer_service": {
            "india": "1-800-180-1407",
            "international": "+91-124-264-1407"
        },
        "website": "https://www.airindia.com"
    }


def apply_styles():
    """Apply CSS styles to the app"""
    st.markdown(UIConstants.MAIN_STYLES, unsafe_allow_html=True)


def display_header():
    """Display main header"""
    st.markdown(f"""
    <div class="main-header">
        <h1 style="margin:0; font-size: 2.5rem;">✈️ {UIConstants.SYSTEM_INFO['company']} Assistant</h1>
        <p style="margin:5px 0 0 0; font-size: 1.1rem; opacity: 0.9;">{UIConstants.SYSTEM_INFO['assistant_name']} AI - {UIConstants.SYSTEM_INFO['version']}</p>
    </div>
    """, unsafe_allow_html=True)


def display_message(message: dict):
    """
    Display a single message in chat format

    Args:
        message: dict with 'role' and 'content' keys
    """
    if message["role"] == "user":
        st.markdown(f'<div class="chat-user"><b>You:</b> {message["content"]}</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-bot"><b>Maharaja:</b> {message["content"]}</div>',
                    unsafe_allow_html=True)


def display_chat_history(messages: list):
    """
    Display entire chat history

    Args:
        messages: list of message dictionaries
    """
    with st.container():
        for message in messages:
            display_message(message)


def create_quick_question_buttons():
    """
    Create quick question buttons
    Returns: st.session_state key if button clicked
    """
    st.subheader("🚀 Quick Questions")
    st.markdown("Click any question for immediate response:")

    cols_per_row = 3
    for i in range(0, len(UIConstants.QUICK_QUESTIONS), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx < len(UIConstants.QUICK_QUESTIONS):
                with cols[j]:
                    question = UIConstants.QUICK_QUESTIONS[idx]
                    if st.button(question, key=f"q{idx}"):
                        clean_question = question.split(" ", 1)[1] if " " in question else question
                        return clean_question
    return None


def create_chat_input():
    """
    Create chat input area
    Returns: (user_input, send_button_pressed)
    """
    col_input, col_button = st.columns([5, 1])

    with col_input:
        user_input = st.text_input(
            "Type your message:",
            placeholder="Example: 'DEL to BOM flights' or 'baggage allowance for international flights'",
            key="user_input_text",
            label_visibility="collapsed"
        )

    with col_button:
        st.markdown("<div style='height: 52px; display: flex; align-items: center;'>", unsafe_allow_html=True)
        send_button = st.button("Send ✈️", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    return user_input, send_button


def display_system_status(components: dict):
    """
    Display system status in sidebar with nice styling like original

    Args:
        components: dict with component status
    """
    st.markdown("**Component Status:**")

    col1, col2 = st.columns(2)

    with col1:
        # Chatbot Engine
        if components.get("chatbot_engine"):
            st.success("✅ Chatbot Engine")
        else:
            st.error("❌ Chatbot Engine")

        # Response Builder
        if components.get("response_builder"):
            st.success("✅ Response Builder")
        else:
            st.error("❌ Response Builder")

        # Intent Detector
        if components.get("intent_detector"):
            st.success("✅ Intent Detector")
        else:
            st.error("❌ Intent Detector")

    with col2:
        # Flight Database
        if components.get("flight_db"):
            st.success("✅ Flight Database")
        else:
            st.warning("⚠️ Flight Database")

        # RAG System
        rag_handler = components.get("rag_handler")
        if rag_handler and hasattr(rag_handler, 'is_initialized') and rag_handler.is_initialized:
            st.success("✅ RAG System")
        else:
            st.warning("⚠️ RAG System")

        # LLM info - styled like original
        st.info(f"**LLM:** phi3:mini")


def display_debug_logs(debug_logs: list, max_lines: int = 15):
    """
    Display debug logs

    Args:
        debug_logs: list of log entries
        max_lines: maximum lines to display
    """
    if debug_logs:
        logs = debug_logs[-max_lines:]
        html_lines = []

        for log in logs:
            if "[ERROR]" in log:
                html_lines.append(f'<span class="debug-error">{log}</span>')
            elif "[WARNING]" in log:
                html_lines.append(f'<span class="debug-warning">{log}</span>')
            elif "[SUCCESS]" in log:
                html_lines.append(f'<span class="debug-success">{log}</span>')
            elif "[TIMER]" in log:
                html_lines.append(f'<span class="debug-time">{log}</span>')
            else:
                html_lines.append(f'<span>{log}</span>')

        logs_html = "<br>".join(html_lines)
        st.markdown(f'<div class="debug-info">{logs_html}</div>', unsafe_allow_html=True)
    else:
        st.info("No debug logs yet. Send a query to see logs.")


def display_footer():
    """Display app footer"""
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: #666; font-size: 0.9em;'>"
        f"✈️ {UIConstants.SYSTEM_INFO['company']} Assistant | {UIConstants.SYSTEM_INFO['version']} | See sidebar for system status"
        "</div>",
        unsafe_allow_html=True
    )


def create_export_button(messages: list, filename_prefix: str = "airindia_chat"):
    """
    Create export conversation button

    Args:
        messages: list of message dictionaries
        filename_prefix: prefix for exported file
    """
    if len(messages) > 1:
        export_text = f"{UIConstants.SYSTEM_INFO['company']} Assistant Conversation\n"
        export_text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        export_text += f"Architecture: {UIConstants.SYSTEM_INFO['version']}\n\n"

        for msg in messages:
            if msg["role"] == "user":
                export_text += f"YOU: {msg['content']}\n\n"
            else:
                export_text += f"MAHARAJA: {msg['content']}\n\n"

        st.download_button(
            label="📥 Download Chat",
            data=export_text,
            file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )


# Test the components
if __name__ == "__main__":
    st.set_page_config(page_title="UI Components Test", page_icon="✈️")
    apply_styles()
    display_header()

    st.subheader("Test Components")

    # Test message display
    test_messages = [
        {"role": "user", "content": "Hello, this is a test message from user!"},
        {"role": "assistant", "content": "Hello! I'm Maharaja, this is a test response from assistant!"}
    ]

    st.write("Test Message Display:")
    for msg in test_messages:
        display_message(msg)

    # Test quick questions
    st.write("Test Quick Questions:")
    clicked = create_quick_question_buttons()
    if clicked:
        st.write(f"Clicked: {clicked}")

    # Test chat input
    st.write("Test Chat Input:")
    user_input, send_button = create_chat_input()
    if send_button:
        st.write(f"Send button pressed with: {user_input}")
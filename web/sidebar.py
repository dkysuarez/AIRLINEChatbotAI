"""
Sidebar Components for Air India Chatbot
=========================================
Sidebar with system controls, debug panel, and utilities.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
import time


class SidebarManager:
    """Manages sidebar components and functionality"""

    def __init__(self, debug_logs_key: str = "debug_logs"):
        """
        Initialize sidebar manager

        Args:
            debug_logs_key: Session state key for debug logs
        """
        self.debug_logs_key = debug_logs_key

    def display_sidebar_header(self):
        """Display sidebar header"""
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #d32f2f; margin-bottom: 5px;">⚙️ System Panel</h2>
            <p style="color: #666; font-size: 0.9em;">Modular Architecture v1.0</p>
            <hr style="margin: 10px 0;">
        </div>
        """, unsafe_allow_html=True)

    def display_system_status_panel(self, components: Dict[str, Any]):
        """
        Display system status panel with nice styling

        Args:
            components: Dictionary with component status
        """
        with st.expander("📊 System Status", expanded=True):
            # Import display_system_status from components
            from .components import display_system_status
            display_system_status(components)

            # Display additional stats if available
            if "chatbot_engine" in components and components["chatbot_engine"]:
                try:
                    stats = components["chatbot_engine"].get_stats_summary()

                    # Create metrics with better styling
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Total Queries:** {stats.get('total_queries', 0)}")
                    with col2:
                        avg_time = stats.get('avg_processing_time', 0)
                        st.info(f"**Avg Time:** {avg_time:.2f}s")

                    # Intent distribution (optional)
                    intent_dist = stats.get("intent_distribution", {})
                    if intent_dist:
                        with st.expander("Intent Distribution", expanded=False):
                            for intent, count in intent_dist.items():
                                st.caption(f"{intent}: {count}")

                except Exception as e:
                    st.warning(f"Could not load performance metrics: {e}")

            # Display message count
            message_count = len(st.session_state.get("messages", []))
            st.info(f"**Messages in chat:** {message_count}")
    def display_debug_panel(self, expanded: bool = True):
        """
        Display debug console panel

        Args:
            expanded: Whether panel is expanded by default
        """
        with st.expander("🔍 Debug Console (LIVE)", expanded=expanded):
            st.markdown("**Real-time Debug Logs:**")

            # Get debug logs from session state
            debug_logs = st.session_state.get(self.debug_logs_key, [])

            # Import display_debug_logs from components
            from .components import display_debug_logs
            display_debug_logs(debug_logs, max_lines=15)

            # Clear logs button
            if st.button("🗑️ Clear Logs", key="clear_logs_btn", use_container_width=True):
                st.session_state[self.debug_logs_key] = []
                st.rerun()

            # Log test button
            if st.button("📝 Add Test Log", key="test_log_btn", use_container_width=True):
                test_log = f"[{datetime.now().strftime('%H:%M:%S')}] [TEST] Test debug log entry"
                if self.debug_logs_key not in st.session_state:
                    st.session_state[self.debug_logs_key] = []
                st.session_state[self.debug_logs_key].append(test_log)
                st.rerun()

    def display_system_tests_panel(self, chat_interface):
        """
        Display system tests panel

        Args:
            chat_interface: ChatInterface instance for processing questions
        """
        st.divider()
        st.markdown("### 🧪 System Tests")

        # Test buttons in columns
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Test Flight", key="test_flight_btn", use_container_width=True):
                st.session_state.pending_question = "DEL to BOM flights"
                st.rerun()

        with col2:
            if st.button("Test RAG", key="test_rag_btn", use_container_width=True):
                st.session_state.pending_question = "Baggage allowance for USA flights"
                st.rerun()

        # Modular system tests
        st.markdown("### 🔄 Modular Tests")

        col3, col4 = st.columns(2)

        with col3:
            if st.button("Test Engine", key="test_engine_btn", use_container_width=True):
                st.session_state.pending_question = "Flights from Delhi to Mumbai"
                st.rerun()

        with col4:
            if st.button("Test Builder", key="test_builder_btn", use_container_width=True):
                st.session_state.pending_question = "What is baggage policy?"
                st.rerun()

    def display_chat_controls(self, chat_interface):
        """
        Display chat controls

        Args:
            chat_interface: ChatInterface instance
        """
        st.divider()
        st.markdown("### 💬 Chat Controls")

        # Clear chat button
        if st.button("🆕 New Chat", key="new_chat_btn", use_container_width=True):
            chat_interface.clear_chat_history()
            st.rerun()

        # Export conversation
        if len(st.session_state.get("messages", [])) > 1:
            # Import create_export_button from components
            from .components import create_export_button
            create_export_button(st.session_state.messages)

    def display_contact_info(self):
        """Display contact information"""
        st.divider()
        st.markdown("""
        ### 📞 Contact & Resources

        **Website:** [airindia.com](https://www.airindia.com)

        **Customer Service:**
        • India: 1-800-180-1407
        • International: +91-124-264-1407

        **Useful Links:**
        • [Baggage Policies](https://www.airindia.com/in/en/travel-information/baggage.html)
        • [Flight Status](https://www.airindia.com/in/en/manage/flight-status.html)
        • [Web Check-in](https://www.airindia.com/in/en/manage/web-check-in.html)

        ---

        *Maharaja AI v4.0*  
        *Modular Architecture with Debug System*
        """)

    def display_performance_metrics(self, chatbot_engine=None):
        """
        Display performance metrics

        Args:
            chatbot_engine: Optional ChatbotEngine instance for stats
        """
        with st.expander("📈 Performance Metrics", expanded=False):

            # Get stats from chatbot engine if available
            if chatbot_engine:
                try:
                    stats = chatbot_engine.get_stats_summary()

                    # Display metrics
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Queries", stats.get("total_queries", 0))
                        st.metric("RAG Available",
                                  "✅" if stats.get("rag_available", False) else "❌")

                    with col2:
                        st.metric("Avg Processing Time",
                                  f"{stats.get('avg_processing_time', 0):.3f}s")

                    # Intent distribution
                    intent_dist = stats.get("intent_distribution", {})
                    if intent_dist:
                        st.markdown("**Intent Distribution:**")
                        for intent, count in intent_dist.items():
                            st.caption(f"{intent}: {count}")

                except Exception as e:
                    st.warning(f"Could not load performance metrics: {e}")

            # Session-based metrics
            if "debug_logs" in st.session_state:
                logs = st.session_state.debug_logs
                error_count = sum(1 for log in logs if "[ERROR]" in log)
                warning_count = sum(1 for log in logs if "[WARNING]" in log)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Session Logs", len(logs))
                with col2:
                    st.metric("Errors/Warnings", f"{error_count}/{warning_count}")

    def display_quick_actions(self):
        """Display quick action buttons"""
        st.divider()
        st.markdown("### ⚡ Quick Actions")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📋 Copy Last Response", key="copy_btn", use_container_width=True):
                if "messages" in st.session_state and st.session_state.messages:
                    last_response = None
                    for msg in reversed(st.session_state.messages):
                        if msg["role"] == "assistant":
                            last_response = msg["content"]
                            break

                    if last_response:
                        st.write("Response copied to clipboard")
                        # Note: Streamlit doesn't have direct clipboard access
                        # This would require JavaScript integration
                    else:
                        st.warning("No assistant response found")

        with col2:
            if st.button("🔄 Restart Session", key="restart_btn", use_container_width=True):
                # Clear session state except essential items
                keys_to_keep = ["app_started", "debug_logs"]
                keys_to_delete = [key for key in st.session_state.keys()
                                  if key not in keys_to_keep]

                for key in keys_to_delete:
                    del st.session_state[key]

                st.rerun()

    def render_full_sidebar(self,
                            components: Dict[str, Any],
                            chat_interface,
                            expanded_sections: Dict[str, bool] = None):
        """
        Render complete sidebar

        Args:
            components: Dictionary with component status
            chat_interface: ChatInterface instance
            expanded_sections: Dictionary with section expanded states
        """
        if expanded_sections is None:
            expanded_sections = {
                "status": True,
                "debug": True,
                "tests": False,
                "metrics": False,
                "controls": False,
                "actions": False,
                "contact": True
            }

        # Display header
        self.display_sidebar_header()

        # Display panels
        self.display_system_status_panel(components)

        st.divider()
        self.display_debug_panel(expanded=expanded_sections.get("debug", True))

        self.display_system_tests_panel(chat_interface)

        if expanded_sections.get("metrics", False):
            self.display_performance_metrics(components.get("chatbot_engine"))

        self.display_chat_controls(chat_interface)

        if expanded_sections.get("actions", False):
            self.display_quick_actions()

        self.display_contact_info()


# Factory function
def create_sidebar_manager(debug_logs_key: str = "debug_logs") -> SidebarManager:
    """
    Create a SidebarManager instance

    Args:
        debug_logs_key: Session state key for debug logs

    Returns:
        SidebarManager instance
    """
    return SidebarManager(debug_logs_key)


if __name__ == "__main__":
    # Test the sidebar
    import streamlit as st

    st.set_page_config(page_title="Sidebar Test", page_icon="✈️", layout="wide")

    # Create test components
    test_components = {
        "chatbot_engine": None,  # Mock
        "response_builder": None,
        "intent_detector": None,
        "flight_db": None,
        "rag_handler": None
    }

    # Initialize debug logs
    if "debug_logs" not in st.session_state:
        st.session_state.debug_logs = [
            "[14:30:25.123] [INFO] Application started",
            "[14:30:26.456] [SUCCESS] Components initialized",
            "[14:30:27.789] [WARNING] RAG system not fully initialized",
            "[14:30:28.012] [ERROR] Test error message",
            "[14:30:29.345] [TIMER] Processing time: 1.234s"
        ]


    # Initialize chat interface mock
    class MockChatInterface:
        def clear_chat_history(self):
            pass


    # Create sidebar manager
    sidebar = create_sidebar_manager()

    # Main content
    st.title("Sidebar Components Test")
    st.write("Check the sidebar for components")

    # Render sidebar
    with st.sidebar:
        sidebar.render_full_sidebar(
            components=test_components,
            chat_interface=MockChatInterface(),
            expanded_sections={
                "status": True,
                "debug": True,
                "tests": True,
                "metrics": True,
                "controls": True,
                "actions": True,
                "contact": True
            }
        )
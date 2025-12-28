"""
Air India Chatbot - Main Application
====================================
Entry point for the modular Air India chatbot.
Minimal app.py that delegates to web modules.
"""

import streamlit as st
import sys
from pathlib import Path
import time
import traceback

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

# Import web modules
try:
    from web.components import apply_styles, display_header, display_footer, UIConstants
    from web.chat_interface import create_chat_interface
    from web.sidebar import create_sidebar_manager

    # Import core components
    from core.chatbot_engine import create_chatbot_engine
    from core.response_builder import create_response_builder
    from core.intent_detector import IntentDetector
    from flight_data.mock_flights import MockFlightDatabase
    from flight_data.context_manager import ConversationContext, IntentType
    from rag.rag_handler import create_rag_handler

    MODULES_AVAILABLE = True
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    traceback.print_exc()
    MODULES_AVAILABLE = False

# ============================================
# CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Air India Assistant",
    page_icon="✈️",
    layout="wide"
)

# Apply CSS styles
apply_styles()


# ============================================
# DEBUG LOGGER (Moved from components for backward compatibility)
# ============================================
class DebugLogger:
    """Utility for detailed debugging"""

    def __init__(self):
        self.logs = []
        self.timers = {}

    def log(self, message: str, level: str = "INFO"):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)

        # Print to console
        print(log_entry)

        # Store in session state for UI display
        if "debug_logs" not in st.session_state:
            st.session_state.debug_logs = []
        st.session_state.debug_logs.append(log_entry)

        # Keep only last 50 logs
        if len(st.session_state.debug_logs) > 50:
            st.session_state.debug_logs = st.session_state.debug_logs[-50:]

    def start_timer(self, name: str):
        self.timers[name] = time.time()
        self.log(f"Timer '{name}' started", "DEBUG")

    def end_timer(self, name: str) -> float:
        if name in self.timers:
            elapsed = time.time() - self.timers[name]
            self.log(f"Timer '{name}': {elapsed:.3f}s", "TIMER")
            del self.timers[name]
            return elapsed
        return 0.0


# Create global debug logger
debug = DebugLogger()


# ============================================
# INITIALIZE COMPONENTS (UPDATED WITH CONTEXT)
# ============================================
@st.cache_resource
def initialize_components():
    """
    Initialize all AI components with detailed debugging.
    Now includes Conversation Context.
    """

    debug.log("=" * 70, "DEBUG")
    debug.log("INITIALIZING AI COMPONENTS (WITH CONTEXT MANAGER)", "DEBUG")
    debug.log("=" * 70, "DEBUG")

    if not MODULES_AVAILABLE:
        debug.log("Required modules not available", "ERROR")
        st.error("Required modules not available.")
        return None, None, None, None, None, None

    try:
        # 1. Conversation Context
        debug.start_timer("context_manager_init")
        debug.log("Creating Conversation Context...", "INFO")
        conversation_context = ConversationContext(
            session_id="user_session_" + str(int(time.time())),
            max_history=15
        )
        debug.end_timer("context_manager_init")
        debug.log("Conversation Context created", "SUCCESS")

        # 2. Intent Detector (con contexto)
        debug.start_timer("intent_detector_init")
        debug.log("Creating Intent Detector with context...", "INFO")
        intent_detector = IntentDetector(
            use_llm_fallback=False,
            context=conversation_context
        )
        debug.end_timer("intent_detector_init")
        debug.log("Intent Detector created with context", "SUCCESS")

        # 3. Main Chatbot Engine
        debug.start_timer("chatbot_engine_init")
        debug.log("Creating Chatbot Engine...", "INFO")
        chatbot_engine = create_chatbot_engine(debug_mode=True)
        debug.end_timer("chatbot_engine_init")
        debug.log("Chatbot Engine created", "SUCCESS")

        # 4. Response Builder
        debug.start_timer("response_builder_init")
        debug.log("Creating Response Builder...", "INFO")
        response_builder = create_response_builder(max_length=2000)
        debug.end_timer("response_builder_init")
        debug.log("Response Builder created", "SUCCESS")

        # 5. Other components
        debug.start_timer("other_components_init")
        debug.log("Initializing other components...", "INFO")

        flight_db = MockFlightDatabase()

        # RAG Handler
        rag_handler = None
        try:
            rag_handler = create_rag_handler()
            if rag_handler and hasattr(rag_handler, 'is_initialized') and rag_handler.is_initialized:
                debug.log("RAG Handler initialized", "SUCCESS")
            else:
                debug.log("RAG Handler not fully initialized", "WARNING")
        except Exception as rag_error:
            debug.log(f"Error initializing RAG Handler: {rag_error}", "ERROR")

        debug.end_timer("other_components_init")
        debug.log("All components initialized", "SUCCESS")

        return chatbot_engine, response_builder, intent_detector, flight_db, rag_handler, conversation_context

    except Exception as e:
        debug.log(f"Critical error initializing components: {e}", "ERROR")
        traceback.print_exc()
        return None, None, None, None, None, None


# Initialize components
debug.log("APP STARTING (WITH CONTEXT MANAGER INTEGRATION)", "INFO")
chatbot_engine, response_builder, intent_detector, flight_db, rag_handler, conversation_context = initialize_components()

# Store context in session state for persistence
if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = conversation_context
    debug.log("Context stored in session state", "INFO")


# ============================================
# RESPONSE FUNCTIONS (IMPROVED WITH BETTER DEBUGGING)
# ============================================
def get_airindia_response(user_query: str) -> str:
    """
    Main chatbot function using modular architecture WITH CONTEXT.
    CON MEJOR DEBUGGING PARA VUELOS.
    """

    debug.log("=" * 70, "DEBUG")
    debug.log(f"🚀 PROCESANDO QUERY: '{user_query}'", "INFO")
    debug.log("=" * 70, "DEBUG")

    if not user_query or not user_query.strip():
        debug.log("Empty query received", "WARNING")
        return "Please enter a question about Air India."

    user_query = user_query.strip()

    try:
        # ====== DEBUG INTENSIVO PARA VUELOS ======
        debug.start_timer("total_processing")

        # 1. DEBUG: Intent detector
        debug.start_timer("intent_detection")
        debug.log(f"Testing intent detector directly...", "DEBUG")

        # Test directo del intent detector
        intent_result = None
        if intent_detector:
            intent_result = intent_detector.detect_intent(user_query)
            debug.log(f"Intent detector result: {intent_result}", "DEBUG")
            debug.log(f"Intent: {intent_result.get('intent', 'N/A')}", "DEBUG")
            debug.log(f"Params keys: {list(intent_result.get('parameters', {}).keys())}", "DEBUG")

            # DEBUG ESPECÍFICO PARA VUELOS
            if intent_result.get('intent') == 'flight_search':
                params = intent_result.get('parameters', {})
                debug.log(f"FLIGHT SEARCH PARAMS:", "CRITICAL")
                debug.log(f"  origin: {params.get('origin')}", "CRITICAL")
                debug.log(f"  destination: {params.get('destination')}", "CRITICAL")
                debug.log(f"  origin_city: {params.get('origin_city')}", "CRITICAL")
                debug.log(f"  destination_city: {params.get('destination_city')}", "CRITICAL")
                debug.log(f"  date: {params.get('date')}", "CRITICAL")
        else:
            debug.log("Intent detector is None!", "ERROR")

        debug.end_timer("intent_detection")

        # 2. Si es búsqueda de vuelos, hacer debug adicional
        if intent_result and intent_result.get('intent') == 'flight_search':
            debug.log("🛫 DETECTADO: FLIGHT SEARCH", "SUCCESS")

            # Debug de parámetros extraídos
            params = intent_result.get('parameters', {})
            origin = params.get('origin')
            destination = params.get('destination')

            if not origin or not destination:
                debug.log("❌ ERROR: Missing origin/destination in params", "ERROR")
                debug.log(f"  Params: {params}", "ERROR")

                # Intentar extracción manual
                debug.log("Intentando extracción manual...", "DEBUG")
                from flight_data.utils import extract_flight_parameters
                manual_params = extract_flight_parameters(user_query)
                debug.log(f"Manual extraction: {manual_params}", "DEBUG")

                # Usar los manuales si son válidos
                if manual_params.get('origin') and manual_params.get('destination'):
                    debug.log("✅ Usando parámetros manuales", "SUCCESS")
                    if 'parameters' not in intent_result:
                        intent_result['parameters'] = {}
                    intent_result['parameters'].update(manual_params)

        # Get conversation context from session state
        context_manager = st.session_state.get("conversation_context")

        if context_manager:
            if context_manager.last_intent:
                debug.log(f"Using conversation context. Last intent: {context_manager.last_intent}", "INFO")
            else:
                debug.log("Using conversation context. No previous intent.", "INFO")

        # Use the ChatbotEngine
        if chatbot_engine is None:
            debug.log("Chatbot Engine not available, using fallback", "ERROR")
            return get_fallback_response(user_query)

        # Get conversation history from context if available
        conversation_history = []
        if context_manager and context_manager.history:
            for msg in context_manager.history[-5:]:
                intent_value = None
                if msg.intent:
                    if hasattr(msg.intent, 'value'):
                        intent_value = msg.intent.value
                    elif isinstance(msg.intent, str):
                        intent_value = msg.intent
                    else:
                        intent_value = str(msg.intent) if msg.intent else None

                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content,
                    "intent": intent_value
                })
            debug.log(f"Using {len(conversation_history)} messages from context", "INFO")

        # ====== PARCHE DE EMERGENCIA PARA VUELOS ======
        # Si es búsqueda de vuelos y el chatbot engine falla, usar simulador directo
        if intent_result and intent_result.get('intent') == 'flight_search':
            params = intent_result.get('parameters', {})
            origin = params.get('origin')
            destination = params.get('destination')
            date = params.get('date', 'tomorrow')

            if origin and destination:
                debug.log(f"🛫 PARCHE ACTIVADO: Buscando vuelos {origin}->{destination}", "INFO")

                try:
                    # Usar simulador directamente
                    from flight_data.flight_simulator import FlightSimulator
                    simulator = FlightSimulator()

                    debug.start_timer("direct_flight_search")
                    flight_result = simulator.search_flights(origin, destination, date)
                    debug.end_timer("direct_flight_search")

                    if flight_result.get('success', False):
                        formatted_response = simulator.format_flight_response(flight_result)
                        debug.log(f"✅ Vuelos encontrados: {len(flight_result.get('flights', []))}", "SUCCESS")

                        # Actualizar contexto si existe
                        if context_manager:
                            flights = flight_result.get('flights', [])
                            if flights:
                                context_manager.update_flight_results(flights)
                                debug.log(f"Context updated with {len(flights)} flights", "INFO")

                        return formatted_response + f"\n\n*[Direct flight search - {len(flight_result.get('flights', []))} flights]*"
                    else:
                        debug.log(f"❌ No flights found in direct search", "WARNING")
                        return f"✈️ No flights available from {origin} to {destination} on {date}."

                except Exception as sim_error:
                    debug.log(f"Error in direct flight search: {sim_error}", "ERROR")
                    # Continuar con procesamiento normal

        # Process query through ChatbotEngine WITH CONTEXT
        debug.start_timer("chatbot_engine_process")
        chatbot_response = chatbot_engine.process_query(
            user_query=user_query,
            conversation_history=conversation_history,
            context_manager=context_manager
        )
        debug.end_timer("chatbot_engine_process")

        debug.log(f"ChatbotEngine response: {chatbot_response.intent} "
                  f"(confidence: {chatbot_response.confidence:.2f})", "SUCCESS")

        # DEBUG del raw_data
        if chatbot_response.raw_data:
            debug.log(f"Raw data type: {chatbot_response.raw_data.get('type', 'N/A')}", "DEBUG")
            if chatbot_response.raw_data.get('type') == 'error':
                debug.log(f"Error message: {chatbot_response.raw_data.get('message', 'N/A')}", "ERROR")

        # If ResponseBuilder is available, use it for formatting
        if response_builder:
            debug.start_timer("response_builder_format")
            formatted_response = response_builder.build_response(
                intent=chatbot_response.intent,
                action_result=chatbot_response.raw_data or {},
                user_query=user_query
            )
            debug.end_timer("response_builder_format")
        else:
            debug.log("ResponseBuilder not available, using raw response", "WARNING")
            formatted_response = chatbot_response.raw_response

        # Update context with assistant's response
        if context_manager:
            try:
                intent_type = None
                if chatbot_response.intent:
                    try:
                        intent_str = chatbot_response.intent.upper()
                        intent_mapping = {
                            'FLIGHT_SEARCH': IntentType.FLIGHT_SEARCH,
                            'POLICY_QUESTION': IntentType.POLICY_QUESTION,
                            'GENERAL_CHAT': IntentType.GENERAL_CHAT,
                            'UNKNOWN': IntentType.UNKNOWN
                        }

                        if intent_str in intent_mapping:
                            intent_type = intent_mapping[intent_str]
                        else:
                            intent_type = IntentType.GENERAL_CHAT
                    except Exception as e:
                        debug.log(f"Could not convert intent '{chatbot_response.intent}' to IntentType: {e}", "WARNING")
                        intent_type = IntentType.GENERAL_CHAT
                else:
                    intent_type = IntentType.GENERAL_CHAT

                context_manager.add_message(
                    role="assistant",
                    content=formatted_response,
                    intent=intent_type,
                    parameters=chatbot_response.raw_data
                )

                # Update flight results if this was a flight search
                if chatbot_response.intent == "flight_search":
                    if chatbot_response.raw_data and chatbot_response.raw_data.get("type") == "flight_results":
                        flights = chatbot_response.raw_data.get("data", {}).get("flights", [])
                        if flights:
                            context_manager.update_flight_results(flights)
                            debug.log(f"Updated context with {len(flights)} flight results", "INFO")

                debug.log(f"Context updated. Total messages: {len(context_manager.history)}", "INFO")

            except Exception as context_error:
                debug.log(f"Error updating context: {context_error}", "ERROR")
                traceback.print_exc()

        # Add processing time info for debug
        total_time = debug.end_timer("total_processing")
        if total_time:
            time_info = f"\n\n*[Processed in {total_time:.1f}s]*"
            formatted_response += time_info

        return formatted_response

    except Exception as e:
        debug.log(f"❌ ERROR in modular processing: {e}", "ERROR")
        traceback.print_exc()

        # Fallback directo para vuelos
        if "flight" in user_query.lower() or "fly" in user_query.lower():
            try:
                debug.log("Attempting emergency flight search...", "INFO")
                from flight_data.utils import extract_flight_parameters
                from flight_data.flight_simulator import FlightSimulator

                params = extract_flight_parameters(user_query)
                if params.get('origin') and params.get('destination'):
                    simulator = FlightSimulator()
                    result = simulator.search_flights(
                        params['origin'],
                        params['destination'],
                        params.get('date', 'tomorrow')
                    )
                    return simulator.format_flight_response(result) + "\n\n*[Emergency response]*"
            except:
                pass

        return get_fallback_response(user_query)


def get_fallback_response(user_query: str) -> str:
    """Fallback when systems are not available."""
    debug.log("Generating fallback response", "INFO")

    # Respuesta rápida para políticas (evitar RAG lento)
    user_lower = user_query.lower()

    if "baggage" in user_lower or "policy" in user_lower:
        return """🧳 **AIR INDIA BAGGAGE INFORMATION**
        
For detailed baggage policies:
• **Website:** https://www.airindia.com/in/en/travel-information/baggage.html
• **Phone:** 1-800-180-1407

*Quick response - full details available on website*"""

    if "flight" in user_lower or "fly" in user_lower:
        return """✈️ **AIR INDIA FLIGHT INFORMATION**
        
For flight bookings and information:
• **Website:** https://www.airindia.com
• **Phone:** 1-800-180-1407
• **App:** Air India mobile app

*Quick response*"""

    if "maharaja" in user_lower or "loyalty" in user_lower:
        return """🏆 **MAHARAJA CLUB**
        
For loyalty program details:
• **Website:** https://www.airindia.com/maharaja-club
• **Phone:** 1-800-180-1407

*Quick response*"""

    # Si no es ninguna de las anteriores, usar Ollama
    try:
        import ollama

        basic_context = """Air India is the national airline of India.

Key Information:
• Checked baggage: Typically 23kg international, 15kg domestic
• Carry-on: 7kg maximum
• Online check-in: 48 hours before departure
• Airport check-in: Closes 60min (international) / 45min (domestic)

For detailed policies: https://www.airindia.com"""

        prompt = f"""You are 'Maharaja', the official Air India assistant.

BASIC AIR INDIA INFORMATION:
{basic_context}

USER QUESTION: {user_query}

Respond helpfully and professionally in English."""

        debug.start_timer("ollama_fallback")
        response = ollama.chat(
            model='phi3:mini',
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3, "num_predict": 250}
        )
        debug.end_timer("ollama_fallback")

        answer = response['message']['content'].strip()
        debug.log(f"Fallback response generated: {len(answer)} chars", "SUCCESS")
        return answer
    except Exception as e:
        debug.log(f"Error in Ollama fallback: {e}", "ERROR")
        return "Hello! I'm Maharaja, your Air India assistant. How can I help you today?"


# ============================================
# INITIALIZE UI MANAGERS
# ============================================
# Create chat interface
chat_interface = create_chat_interface()

# Create sidebar manager
sidebar_manager = create_sidebar_manager()


# ============================================
# MAIN UI
# ============================================
# Display header
display_header()

# Main container
with st.container():
    # Quick questions section
    from web.components import create_quick_question_buttons

    quick_question = create_quick_question_buttons()

    # If quick question was clicked
    if quick_question:
        debug.log(f"Quick question button: '{quick_question}'", "INFO")
        chat_interface.process_quick_question(quick_question, get_airindia_response)
        st.rerun()

    st.divider()

    # Display chat area
    chat_interface.display_chat_area()

    st.divider()

    # Chat input
    from web.components import create_chat_input

    user_input, send_button = create_chat_input()


# ============================================
# PROCESS TEXT INPUT
# ============================================
if send_button and user_input:
    debug.log(f"User text input: '{user_input}'", "INFO")
    chat_interface.process_text_input(user_input, True, get_airindia_response)
    st.rerun()


# ============================================
# SIDEBAR (UPDATED WITH CONTEXT CONTROLS)
# ============================================
with st.sidebar:
    # Prepare components dictionary for sidebar
    components_dict = {
        "chatbot_engine": chatbot_engine,
        "response_builder": response_builder,
        "intent_detector": intent_detector,
        "flight_db": flight_db,
        "rag_handler": rag_handler,
        "conversation_context": st.session_state.get("conversation_context")
    }

    # Render complete sidebar with context controls
    sidebar_manager.render_full_sidebar(
        components=components_dict,
        chat_interface=chat_interface,
        expanded_sections={
            "status": True,
            "debug": True,
            "tests": False,
            "metrics": False,
            "controls": True,
            "actions": False,
            "contact": True
        }
    )

    # Add context-specific controls
    st.divider()
    st.markdown("### 🧠 Conversation Context")

    # Clear context button
    if st.button("🗑️ Clear Context Only", key="main_clear_context_btn", use_container_width=True):
        if "conversation_context" in st.session_state:
            st.session_state.conversation_context.clear()
            st.success("Context cleared! Conversation history remains.")
            debug.log("Context cleared manually", "INFO")
            st.rerun()

    # Show context stats
    if "conversation_context" in st.session_state:
        ctx = st.session_state.conversation_context
        summary = ctx.get_conversation_summary()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Messages", summary['message_count'])
        with col2:
            st.metric("Flights", summary['flight_results_count'])

        # Show last intent
        if summary['last_intent']:
            st.caption(f"**Last intent:** {summary['last_intent']}")

        # Debug: Show context details
        if st.checkbox("Show Context Details", key="main_show_context_details"):
            st.json(summary)


# ============================================
# FOOTER
# ============================================
display_footer()


# ============================================
# HANDLE PENDING QUESTIONS (from sidebar tests)
# ============================================
if "pending_question" in st.session_state:
    pending_question = st.session_state.pending_question
    del st.session_state.pending_question

    debug.log(f"Processing pending question: '{pending_question}'", "INFO")
    chat_interface.process_quick_question(pending_question, get_airindia_response)
    st.rerun()


# Initial debug message
if "app_started" not in st.session_state:
    debug.log("Application started successfully with Context Manager", "SUCCESS")
    st.session_state.app_started = True
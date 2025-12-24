import streamlit as st
import ollama

# Configuración de la página
st.set_page_config(page_title="Maharaja - Air India", page_icon="🛫")
st.title("🛫 Maharaja - Asistente de Air India")
st.markdown("**¡Namaste!** Soy Maharaja, tu asistente personal de Air India. "
            "Puedo ayudarte con equipaje, check-in, vuelos y más. ✈️")

# Historial de mensajes
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input del usuario
if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
    # Añadir mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar respuesta
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            # System prompt con personalidad de Air India
            system_message = {
                "role": "system",
                "content": "Eres Maharaja, un asistente amable, profesional y útil de Air India. "
                           "Responde siempre en español o inglés según el idioma del usuario. "
                           "Sé claro, preciso y ofrece más ayuda al final. "
                           "Usa emojis relacionados con viajes cuando sea adecuado. "
                           "Si no estás seguro de algo, recomienda visitar www.airindia.com."
            }

            # Historial completo para el modelo
            messages = [system_message] + st.session_state.messages

            # Llamada a Ollama con streaming
            stream = ollama.chat(
                model='phi3:mini',  # Cambia aquí si usas otro modelo (ej: llama3.2:1b)
                messages=messages,
                stream=True
            )

            # Mostrar respuesta letra por letra
            response = st.write_stream(chunk['message']['content'] for chunk in stream)

    # Guardar respuesta del asistente
    st.session_state.messages.append({"role": "assistant", "content": response})
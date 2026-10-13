import streamlit as st
from groq_tracker import ask_groq
from usage_logger import log_usage

st.set_page_config(
    page_title="LLM Playground",
    page_icon="💬",
    layout="wide",
)

# Minimal chat interface styling
st.markdown(
    """
    <style>
    .block-container {
        max-width: 900px;
        padding-top: 1.5rem;
        padding-bottom: 1rem;
    }

    [data-testid="stChatMessage"] {
        border-radius: 12px;
        padding: 1rem;
    }

    [data-testid="stChatInput"] {
        max-width: 900px;
        margin: 0 auto;
    }

    .subtitle {
        color: #888888;
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("LLM Playground")
st.markdown(
    '<div class="subtitle">Ask questions and explore AI with Groq.</div>',
    unsafe_allow_html=True,
)

# Keep conversation history across Streamlit reruns
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Persistent chat input for the next request
prompt = st.chat_input("Message the AI...")

if prompt:
    # Display and store the user's message immediately
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate the response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = ask_groq(prompt)
                answer = result["answer"]

                # Log usage for the separate dashboard
                log_usage(result)

                st.markdown(answer)

                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

            except Exception as error:
                error_message = f"Request failed: {error}"
                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )

# Small utility at the bottom, rather than cost metrics
if st.session_state.messages:
    st.divider()

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()



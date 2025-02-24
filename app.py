import streamlit as st
from chat_manager import ChatManager
from config_manager import ConfigManager
from api_client import APIClient
import json

def initialize_session_state():
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'config' not in st.session_state:
        st.session_state.config = ConfigManager.get_default_config()

def main():
    st.set_page_config(
        page_title="Proxy Chat App",
        page_icon="💬",
        layout="wide"
    )
    
    initialize_session_state()
    
    # Sidebar configuration
    with st.sidebar:
        st.title("⚙️ Settings")
        
        # Proxy Configuration
        st.subheader("Proxy Settings")
        proxy_url = st.text_input(
            "Proxy URL",
            value=st.session_state.config.get('proxy_url', ''),
            placeholder="http://proxy.example.com:8080"
        )
        
        # API Configuration
        st.subheader("API Settings")
        api_endpoint = st.text_input(
            "API Endpoint",
            value=st.session_state.config.get('api_endpoint', ''),
            placeholder="https://api.example.com/chat"
        )
        
        # Search Parameters
        st.subheader("Search Parameters")
        retrieval_mode = st.selectbox(
            "Retrieval Mode",
            options=["hybrid", "text", "vectors"],
            index=0
        )
        
        top_k = st.slider("Top K Documents", 1, 20, 5)
        
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
        
        # Advanced Settings
        with st.expander("Advanced Settings"):
            semantic_ranker = st.checkbox("Use Semantic Ranker", value=True)
            semantic_captions = st.checkbox("Use Semantic Captions", value=True)
            followup_questions = st.checkbox("Suggest Followup Questions", value=True)
        
        # Save Configuration
        if st.button("Save Settings"):
            new_config = {
                'proxy_url': proxy_url,
                'api_endpoint': api_endpoint,
                'retrieval_mode': retrieval_mode,
                'top_k': top_k,
                'temperature': temperature,
                'semantic_ranker': semantic_ranker,
                'semantic_captions': semantic_captions,
                'followup_questions': followup_questions
            }
            ConfigManager.save_config(new_config)
            st.session_state.config = new_config
            st.success("Settings saved successfully!")

    # Main chat interface
    st.title("💬 Proxy Chat")
    
    # Chat history
    chat_manager = ChatManager()
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant" and "context" in message:
                with st.expander("View Sources"):
                    st.json(message["context"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # User message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get response
        try:
            api_client = APIClient(st.session_state.config)
            response = api_client.send_message(st.session_state.chat_history)
            
            if response.get("error"):
                st.error(f"Error: {response['error']}")
            else:
                message = response["message"]
                st.session_state.chat_history.append({
                    "role": message["role"],
                    "content": message["content"],
                    "context": response.get("context", {})
                })
                
                with st.chat_message("assistant"):
                    st.write(message["content"])
                    if response.get("context"):
                        with st.expander("View Sources"):
                            st.json(response["context"])
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()

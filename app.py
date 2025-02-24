import streamlit as st
from chat_manager import ChatManager
from config_manager import ConfigManager
from api_client import APIClient
import json
from datetime import datetime

def initialize_session_state():
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'config' not in st.session_state:
        st.session_state.config = ConfigManager.get_default_config()
    if 'current_thread_id' not in st.session_state:
        st.session_state.current_thread_id = None
    if 'chat_manager' not in st.session_state:
        st.session_state.chat_manager = ChatManager()
    if 'api_client' not in st.session_state:
        st.session_state.api_client = APIClient(st.session_state.config)
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False

def format_datetime(iso_string):
    """ISO形式の日時文字列を読みやすい形式に変換"""
    dt = datetime.fromisoformat(iso_string)
    return dt.strftime("%Y/%m/%d %H:%M")

def main():
    st.set_page_config(
        page_title="Proxy Chat App",
        page_icon="💬",
        layout="wide"
    )

    initialize_session_state()
    chat_manager = st.session_state.chat_manager

    # サイドバーの設定
    with st.sidebar:
        st.title("⚙️ Settings")

        # デバッグモード設定
        debug_mode = st.checkbox("🐛 Debug Mode", value=st.session_state.debug_mode)
        if debug_mode != st.session_state.debug_mode:
            st.session_state.debug_mode = debug_mode
            st.rerun()

        # チャットスレッド管理
        st.subheader("📑 Chat Threads")

        # 新規スレッド作成
        new_thread_title = st.text_input("New Thread Title", placeholder="Enter thread title...")
        if st.button("Create New Thread"):
            thread_info = chat_manager.create_thread(new_thread_title)
            st.session_state.current_thread_id = thread_info['id']
            st.session_state.chat_history = []
            # 新しいスレッドを作成したら、APIClientも新しく初期化
            st.session_state.api_client = APIClient(st.session_state.config)
            st.success(f"Created new thread: {thread_info['title']}")
            st.rerun()

        # スレッド一覧
        st.subheader("Threads")
        threads = chat_manager.list_threads()
        for thread in sorted(threads, key=lambda x: x['updated_at'], reverse=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(
                    f"📄 {thread['title']}",
                    key=f"thread_{thread['id']}",
                    help=f"Created: {format_datetime(thread['created_at'])}\nUpdated: {format_datetime(thread['updated_at'])}"
                ):
                    st.session_state.current_thread_id = thread['id']
                    st.session_state.chat_history = chat_manager.get_thread_history(thread['id'])
                    # スレッドを切り替えたとき、保存されているセッション状態を復元
                    session_state = chat_manager.get_thread_session_state(thread['id'])
                    if session_state:
                        st.session_state.api_client.update_session_state(thread['id'], session_state)
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"delete_{thread['id']}", help="Delete this thread"):
                    chat_manager.delete_thread(thread['id'])
                    if st.session_state.current_thread_id == thread['id']:
                        st.session_state.current_thread_id = None
                        st.session_state.chat_history = []
                    st.rerun()

        # デバッグ情報表示
        if st.session_state.debug_mode:
            with st.expander("🔍 Debug Info", expanded=True):
                st.subheader("Session States")
                st.json(st.session_state.api_client.session_states)
                st.subheader("Current Thread ID")
                st.code(st.session_state.current_thread_id)

        st.divider()

        # その他の設定
        st.subheader("Proxy Settings")
        proxy_url = st.text_input(
            "Proxy URL",
            value=st.session_state.config.get('proxy_url', ''),
            placeholder="http://proxy.example.com:8080"
        )

        st.subheader("API Settings")
        api_endpoint = st.text_input(
            "API Endpoint",
            value=st.session_state.config.get('api_endpoint', ''),
            placeholder="https://api.example.com/chat"
        )

        st.subheader("Search Parameters")
        retrieval_mode = st.selectbox(
            "Retrieval Mode",
            options=["hybrid", "text", "vectors"],
            index=0
        )

        top_k = st.slider("Top K Documents", 1, 20, 5)
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7)

        st.subheader("Advanced Settings")
        with st.expander("Advanced Settings", expanded=False):
            semantic_ranker = st.checkbox("Use Semantic Ranker", value=True)
            semantic_captions = st.checkbox("Use Semantic Captions", value=True)
            followup_questions = st.checkbox("Suggest Followup Questions", value=True)

            st.subheader("Prompt Template")
            prompt_template = st.text_area(
                "Prompt Template",
                value=st.session_state.config.get('prompt_template', ''),
                help="Enter the prompt template to be used for generating responses",
                height=150
            )

        if st.button("Save Settings"):
            new_config = {
                'proxy_url': proxy_url,
                'api_endpoint': api_endpoint,
                'retrieval_mode': retrieval_mode,
                'top_k': top_k,
                'temperature': temperature,
                'semantic_ranker': semantic_ranker,
                'semantic_captions': semantic_captions,
                'followup_questions': followup_questions,
                'prompt_template': prompt_template
            }
            ConfigManager.save_config(new_config)
            st.session_state.config = new_config
            st.session_state.api_client = APIClient(new_config)  # APIクライアントを新しい設定で再初期化
            st.success("Settings saved successfully!")

    # メインチャットインターフェース
    st.title("💬 Proxy Chat")

    # 現在のスレッド情報を表示
    if st.session_state.current_thread_id:
        thread_info = next(
            (t for t in chat_manager.list_threads() if t['id'] == st.session_state.current_thread_id),
            None
        )
        if thread_info:
            st.caption(f"Current Thread: {thread_info['title']}")

            # デバッグ情報表示
            if st.session_state.debug_mode:
                with st.expander("🔍 Current Thread Debug Info", expanded=True):
                    st.json({
                        "thread_id": st.session_state.current_thread_id,
                        "session_state": st.session_state.api_client.session_states.get(st.session_state.current_thread_id)
                    })
    else:
        st.caption("No thread selected. Please create or select a thread from the sidebar.")

    # チャット履歴の表示
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant":
                if "context" in message:
                    col1, col2 = st.columns(2)
                    with col1:
                        with st.expander("データポイント"):
                            if "data_points" in message["context"]:
                                for point in message["context"]["data_points"]:
                                    st.write(point["text"])
                    with col2:
                        with st.expander("過去のやりとり"):
                            if "chat_history" in message["context"]:
                                st.text(message["context"]["chat_history"])

    # チャット入力（スレッドが選択されている場合のみ有効）
    if st.session_state.current_thread_id:
        if prompt := st.chat_input("Type your message here..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            try:
                response = st.session_state.api_client.send_message(
                    st.session_state.chat_history,
                    thread_id=st.session_state.current_thread_id
                )

                if response.get("error"):
                    st.error(f"Error: {response['error']}")
                else:
                    message = response["message"]
                    st.session_state.chat_history.append({
                        "role": message["role"],
                        "content": message["content"],
                        "context": response.get("context", {})
                    })

                    # スレッドの履歴を保存
                    chat_manager.save_thread_history(
                        st.session_state.current_thread_id,
                        st.session_state.chat_history
                    )

                    # セッション状態を保存
                    if response.get("session_state"):
                        chat_manager.update_thread_session_state(
                            st.session_state.current_thread_id,
                            response["session_state"]
                        )

                    with st.chat_message("assistant"):
                        st.write(message["content"])
                        if response.get("context"):
                            col1, col2 = st.columns(2)
                            with col1:
                                with st.expander("データポイント"):
                                    if "data_points" in response["context"]:
                                        for point in response["context"]["data_points"]:
                                            st.write(point["text"])
                            with col2:
                                with st.expander("過去のやりとり"):
                                    if "chat_history" in response["context"]:
                                        st.text(response["context"]["chat_history"])

                        # デバッグモードの場合、APIリクエスト/レスポンス情報を表示
                        if st.session_state.debug_mode:
                            with st.expander("🔍 API Debug Info", expanded=True):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.subheader("Request")
                                    st.json(st.session_state.api_client.last_request)
                                with col2:
                                    st.subheader("Response")
                                    st.json(st.session_state.api_client.last_response)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.info("Please select or create a thread to start chatting.")

if __name__ == "__main__":
    main()
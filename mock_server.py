from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import json
from typing import Dict, List, Optional
import os

class SessionManager:
    def __init__(self):
        self.sessions_dir = "mock_sessions"
        self._ensure_sessions_directory()
        self.sessions: Dict[str, List[dict]] = {}
        self._load_sessions()

    def _ensure_sessions_directory(self):
        """セッション保存用のディレクトリを作成"""
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)

    def _get_session_file_path(self, thread_id: str) -> str:
        """セッションファイルのパスを取得"""
        return os.path.join(self.sessions_dir, f"{thread_id}.json")

    def _load_sessions(self):
        """保存されているセッションを読み込む"""
        if not os.path.exists(self.sessions_dir):
            return

        for file_name in os.listdir(self.sessions_dir):
            if file_name.endswith('.json'):
                thread_id = file_name[:-5]  # .jsonを除去
                try:
                    with open(os.path.join(self.sessions_dir, file_name), 'r', encoding='utf-8') as f:
                        self.sessions[thread_id] = json.load(f)
                except Exception as e:
                    print(f"Error loading session {thread_id}: {e}")

    def save_session(self, thread_id: str, messages: List[dict]):
        """セッションを保存"""
        self.sessions[thread_id] = messages
        file_path = self._get_session_file_path(thread_id)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving session {thread_id}: {e}")

    def get_session(self, thread_id: str) -> List[dict]:
        """セッションを取得"""
        return self.sessions.get(thread_id, [])

app = FastAPI()
session_manager = SessionManager()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()

        # スレッドIDの取得（リクエストデータまたはコンテキストから）
        thread_id = data.get("context", {}).get("thread_id")
        if not thread_id:
            return {
                "error": "Thread ID is required"
            }

        # 受信したメッセージを取得
        messages = data.get("messages", [])

        # セッションに保存
        session_manager.save_session(thread_id, messages)

        # 最新の質問を取得
        latest_question = messages[-1]["content"] if messages else "質問が見つかりません"

        # スレッドの全履歴を取得
        thread_history = session_manager.get_session(thread_id)

        # 応答を生成
        main_response = f"スレッド {thread_id} の応答: {latest_question}"

        # 過去のやりとりをフォーマット
        history_text = "\n".join([
            f"{idx}. {msg['role']}: {msg['content']}"
            for idx, msg in enumerate(thread_history, 1)
        ])

        return {
            "message": {
                "role": "assistant",
                "content": main_response
            },
            "context": {
                "thread_id": thread_id,
                "data_points": [
                    {"text": "これはモックの応答です。"}
                ],
                "chat_history": history_text
            }
        }
    except Exception as e:
        return {
            "message": {
                "role": "assistant",
                "content": f"エラーが発生しました: {str(e)}"
            },
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
import logging
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import uuid
from typing import Dict, List, Optional

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS設定を更新
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# セッション情報を保持する辞書
sessions: Dict[str, Dict] = {}

@app.get("/")
async def root():
    """ルートエンドポイントのハンドラ"""
    logger.info("Root endpoint accessed")
    return {"status": "Mock server is running"}

@app.post("/chat")
async def chat(request: Request):
    """チャットリクエストを処理するハンドラ"""
    try:
        # リクエストの詳細をログに記録
        request_headers = dict(request.headers)
        logger.info(f"Received request with headers: {request_headers}")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request path: {request.url.path}")
        logger.info(f"Request method: {request.method}")

        data = await request.json()
        logger.info(f"Received request data: {data}")

        # 受信したメッセージを取得
        messages = data.get("messages", [])

        # セッション状態を取得
        session_state = data.get("session_state")

        # 最新の質問を取得
        latest_question = messages[-1]["content"] if messages else "質問が見つかりません"

        if not session_state:
            # 新規セッションの場合
            session_id = str(uuid.uuid4())
            session_state = {
                "session_id": session_id,
                "message_counter": 1,
                "created_at": datetime.now().isoformat()
            }
            sessions[session_id] = session_state
        else:
            # 既存セッションの場合
            session_id = session_state.get("session_id")
            if session_id in sessions:
                session_state = sessions[session_id]
                session_state["message_counter"] += 1
            else:
                # セッションが見つからない場合は新規作成
                session_id = str(uuid.uuid4())
                session_state = {
                    "session_id": session_id,
                    "message_counter": 1,
                    "created_at": datetime.now().isoformat()
                }
            sessions[session_id] = session_state

        # 過去のやりとりをフォーマット
        history_text = "\n".join([
            f"{idx}. {msg['role']}: {msg['content']}"
            for idx, msg in enumerate(messages, 1)
        ])

        main_response = f"応答 #{session_state['message_counter']}: あなたの質問「{latest_question}」に対する応答です。"

        logger.info(f"Sending response: {main_response}")

        response_data = {
            "message": {
                "role": "assistant",
                "content": main_response
            },
            "context": {
                "data_points": [
                    {"text": "これはモックの応答です。"}
                ],
                "chat_history": history_text
            },
            "session_state": session_state
        }
        logger.info(f"Response data: {response_data}")
        return response_data

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            "message": {
                "role": "assistant",
                "content": f"エラーが発生しました: {str(e)}"
            },
            "error": str(e)
        }

if __name__ == "__main__":
    logger.info("Starting mock server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
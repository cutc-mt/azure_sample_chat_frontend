from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import json
from typing import Dict, List, Optional

app = FastAPI()

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

        # 受信したメッセージを取得
        messages = data.get("messages", [])

        # セッション状態を取得
        session_state = data.get("session_state")

        # 最新の質問を取得
        latest_question = messages[-1]["content"] if messages else "質問が見つかりません"

        # セッション状態の管理
        if not session_state:
            # 新規セッションの場合
            message_counter = 1
            session_state = {"message_counter": message_counter}
        else:
            # 既存セッションの場合
            message_counter = session_state.get("message_counter", 0) + 1
            session_state = {"message_counter": message_counter}

        # 過去のやりとりをフォーマット
        history_text = "\n".join([
            f"{idx}. {msg['role']}: {msg['content']}"
            for idx, msg in enumerate(messages, 1)
        ])

        main_response = f"応答 #{message_counter}: あなたの質問「{latest_question}」に対する応答です。"

        return {
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
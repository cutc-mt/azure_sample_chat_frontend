from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# チャット履歴を保持する辞書
chat_counter = 0
chat_history = []

@app.post("/chat")
async def chat(request: Request):
    global chat_counter
    try:
        data = await request.json()

        # 受信したメッセージを履歴に追加
        messages = data.get("messages", [])
        chat_history.extend(messages)

        # 最新の質問を取得
        latest_question = messages[-1]["content"] if messages else "質問が見つかりません"

        # 通番を増やして応答を生成
        chat_counter += 1
        response = f"応答 #{chat_counter}: あなたの質問「{latest_question}」に対する応答です。\n\n過去のやりとり:\n"

        # 過去のやりとりを含める
        for idx, msg in enumerate(chat_history, 1):
            response += f"{idx}. {msg['role']}: {msg['content']}\n"

        return {
            "message": {
                "role": "assistant",
                "content": response
            },
            "context": {
                "data_points": [
                    {"text": "これはモックの応答です。"}
                ]
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
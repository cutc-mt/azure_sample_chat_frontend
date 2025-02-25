import logging
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import uvicorn
from datetime import datetime
import ssl
from urllib.parse import unquote

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Test Proxy Server")

# プロキシリクエストの履歴
request_history = []

@app.get("/")
async def read_root():
    return {"status": "Proxy server is running"}

@app.get("/history")
async def get_history():
    """プロキシサーバを経由したリクエストの履歴を取得"""
    return request_history

@app.post("/clear-history")
async def clear_history():
    """リクエスト履歴をクリア"""
    request_history.clear()
    return {"status": "History cleared"}

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_handler(request: Request, full_path: str):
    """すべてのリクエストを転送するプロキシハンドラ"""
    try:
        # リクエストの詳細をログに記録
        request_time = datetime.now().isoformat()
        body = await request.body()
        headers = dict(request.headers)
        query_params = str(request.query_params)

        # センシティブな情報を除外
        if "authorization" in headers:
            headers["authorization"] = "***"

        # リクエスト情報を保存
        request_info = {
            "timestamp": request_time,
            "method": request.method,
            "full_path": full_path,
            "query_params": query_params,
            "headers": headers,
            "body": body.decode() if body else None
        }

        logger.info(f"Incoming request: {request_info}")

        # HTTPSクライアントの設定
        client_settings = {
            "timeout": httpx.Timeout(30.0),
            "verify": ssl.CERT_REQUIRED,
            "follow_redirects": True
        }

        # リクエストパスをデコード
        decoded_path = unquote(full_path)
        logger.info(f"Decoded path: {decoded_path}")

        # モックサーバーへのリクエストを構築
        target_url = "http://localhost:8000/chat"
        logger.info(f"Forwarding request to: {target_url}")

        async with httpx.AsyncClient(**client_settings) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )
            response.raise_for_status()

            # レスポンス情報を記録
            response_info = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text
            }

            # 履歴に記録
            request_history.append({
                "request": request_info,
                "response": response_info
            })

            # 最大100件まで履歴を保持
            if len(request_history) > 100:
                request_history.pop(0)

            # レスポンスの処理
            try:
                content = response.json()
            except json.JSONDecodeError:
                content = {"text": response.text}

            logger.info(f"Response received: {content}")
            return JSONResponse(
                content=content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

    except httpx.ProxyError as e:
        logger.error(f"Proxy error details: {str(e)}")
        error_msg = f"Proxy connection failed: {str(e)}"
        raise HTTPException(status_code=502, detail=error_msg)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP status error: {str(e)}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("Starting proxy server on port 3000...")
    uvicorn.run(app, host="0.0.0.0", port=3000)
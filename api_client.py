import requests
import json
from urllib.parse import urlparse
import logging

# ロギングの基本設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class APIClient:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session_states = {}
        self.last_request = None
        self.last_response = None

        # プロキシ設定の処理
        if self.config.get('proxy_url'):
            try:
                proxy_url = self.config['proxy_url'].strip()
                self.logger.info(f"Setting up proxy: {proxy_url}")

                # プロキシURLのスキーム確認と追加
                if not proxy_url.startswith(('http://', 'https://')):
                    proxy_url = 'http://' + proxy_url

                # プロキシURLの検証
                parsed = urlparse(proxy_url)
                if not all([parsed.scheme, parsed.netloc]):
                    raise ValueError(f"Invalid proxy URL format: {proxy_url}")

                # プロキシ設定を適用
                self.session.proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                self.logger.info(f"Proxy configured successfully: {proxy_url}")

            except Exception as e:
                self.logger.error(f"Failed to configure proxy: {str(e)}")
                self.session.proxies = {}

    def validate_api_endpoint(self, endpoint):
        """APIエンドポイントのURLを検証"""
        if not endpoint:
            return False, "API endpoint is not configured"

        try:
            parsed = urlparse(endpoint)
            if not all([parsed.scheme, parsed.netloc]):
                return False, "Invalid API endpoint URL format"
            return True, None
        except Exception as e:
            return False, f"Invalid API endpoint: {str(e)}"

    def send_message(self, chat_history, thread_id=None):
        try:
            # APIエンドポイントの取得と検証
            api_endpoint = self.config.get('api_endpoint', '').strip()
            is_valid, error_msg = self.validate_api_endpoint(api_endpoint)
            if not is_valid:
                raise ValueError(error_msg)

            # チャットエンドポイントの確認
            if not api_endpoint.endswith('/chat'):
                api_endpoint = f"{api_endpoint.rstrip('/')}/chat"

            request_data = self._prepare_request_data(chat_history, thread_id)
            self.last_request = request_data

            self.logger.info("Preparing to send request")
            if self.session.proxies:
                self.logger.info(f"Using proxy configuration: {self.session.proxies}")
            self.logger.info(f"Sending request to: {api_endpoint}")

            # プロキシ設定を使用してリクエストを送信
            response = self.session.post(
                api_endpoint,
                json=request_data,
                headers={
                    'Content-Type': 'application/json'
                },
                timeout=30,
                allow_redirects=True  # リダイレクトを許可
            )

            response.raise_for_status()
            response_data = response.json()
            self.last_response = response_data

            if thread_id:
                self.session_states[thread_id] = response_data.get("session_state")

            return response_data

        except requests.exceptions.ProxyError as e:
            error_msg = f"Proxy connection failed: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response from API: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}

    def _prepare_request_data(self, chat_history, thread_id=None):
        """リクエストデータの準備"""
        return {
            "messages": chat_history,
            "context": {
                "thread_id": thread_id,
                "overrides": {
                    "prompt_template": self.config.get('prompt_template', ''),
                    "retrieval_mode": self.config.get('retrieval_mode', 'hybrid'),
                    "top": self.config.get('top_k', 5),
                    "temperature": self.config.get('temperature', 0.7),
                    "semantic_ranker": self.config.get('semantic_ranker', True),
                    "semantic_captions": self.config.get('semantic_captions', True),
                    "suggest_followup_questions": self.config.get('followup_questions', True)
                }
            },
            "session_state": self.session_states.get(thread_id)
        }

    def update_session_state(self, thread_id, session_state):
        if thread_id:
            self.session_states[thread_id] = session_state
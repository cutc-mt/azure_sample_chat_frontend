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
        self.logger = logging.getLogger(__name__)  # ロガーの初期化を先に行う
        self.session = self._create_session()
        self.session_states = {}  # スレッドIDごとのセッション状態を管理
        self.last_request = None  # デバッグ用：最後のリクエスト内容
        self.last_response = None  # デバッグ用：最後のレスポンス内容

    def _create_session(self):
        session = requests.Session()

        # プロキシ設定の処理
        if self.config.get('proxy_url'):
            try:
                proxy_url = self.config['proxy_url'].strip()

                # プロキシURLのスキーム確認と追加
                if not proxy_url.startswith(('http://', 'https://')):
                    proxy_url = 'http://' + proxy_url

                # プロキシURLの検証
                parsed = urlparse(proxy_url)
                if not all([parsed.scheme, parsed.netloc]):
                    raise ValueError(f"Invalid proxy URL format: {proxy_url}")

                # プロキシ設定を適用
                session.proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }

                self.logger.info(f"Proxy configured: {proxy_url}")

                # SSL証明書の検証設定（オプション）
                verify_ssl = self.config.get('verify_ssl', True)
                session.verify = verify_ssl
                if not verify_ssl:
                    self.logger.warning("SSL certificate verification is disabled")

            except Exception as e:
                self.logger.error(f"Failed to configure proxy: {str(e)}")
                # プロキシ設定に失敗した場合は、プロキシなしで続行
                session.proxies = {}

        return session

    def validate_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def send_message(self, chat_history, thread_id=None):
        if not self.config.get('api_endpoint'):
            raise ValueError("API endpoint not configured")

        if not self.validate_url(self.config['api_endpoint']):
            raise ValueError("Invalid API endpoint URL")

        try:
            request_data = self._prepare_request_data(chat_history, thread_id)
            self.last_request = request_data  # デバッグ用

            # プロキシ使用状況のログ出力
            if self.session.proxies:
                self.logger.info(f"Sending request through proxy: {self.session.proxies}")

            response = self.session.post(
                self.config['api_endpoint'],
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            response_data = response.json()

            self.last_response = response_data  # デバッグ用

            if thread_id:
                self.session_states[thread_id] = response_data.get("session_state")

            return response_data

        except requests.exceptions.ProxyError as e:
            error_msg = f"Proxy connection failed: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
        except requests.exceptions.SSLError as e:
            error_msg = f"SSL verification failed: {str(e)}"
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
        """スレッドのセッション状態を更新"""
        if thread_id:
            self.session_states[thread_id] = session_state
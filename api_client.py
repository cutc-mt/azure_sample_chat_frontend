import requests
import json
from urllib.parse import urlparse

class APIClient:
    def __init__(self, config):
        self.config = config
        self.session = self._create_session()
        self.session_states = {}  # スレッドIDごとのセッション状態を管理

    def _create_session(self):
        session = requests.Session()
        if self.config.get('proxy_url'):
            proxy_url = self.config['proxy_url']
            if not proxy_url.startswith(('http://', 'https://')):
                proxy_url = 'http://' + proxy_url
            session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        return session

    def _prepare_request_data(self, chat_history, thread_id=None):
        return {
            "messages": chat_history,
            "context": {
                "thread_id": thread_id,
                "overrides": {
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
            response = self.session.post(
                self.config['api_endpoint'],
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            response_data = response.json()

            # スレッドIDごとにセッション状態を更新
            if thread_id:
                self.session_states[thread_id] = response_data.get("session_state")

            return response_data

        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            return {"error": error_msg}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from API"}

    def update_session_state(self, thread_id, session_state):
        """スレッドのセッション状態を更新"""
        if thread_id:
            self.session_states[thread_id] = session_state
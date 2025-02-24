import json
from datetime import datetime
import base64
import os
import uuid

class ChatManager:
    def __init__(self):
        self.threads_file = "chat_threads.json"
        self.threads_dir = "chat_threads"
        self._ensure_threads_directory()

    def _ensure_threads_directory(self):
        """スレッド保存用のディレクトリを作成"""
        if not os.path.exists(self.threads_dir):
            os.makedirs(self.threads_dir)

    def _get_thread_file_path(self, thread_id):
        """スレッドファイルのパスを取得"""
        return os.path.join(self.threads_dir, f"{thread_id}.json")

    def create_thread(self, title=None):
        """新しいチャットスレッドを作成"""
        thread_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        thread_info = {
            'id': thread_id,
            'title': title or f"Chat {timestamp}",
            'created_at': timestamp,
            'updated_at': timestamp,
            'session_state': None  # セッション状態の初期化
        }

        # スレッド情報を保存
        self.save_thread_info(thread_info)
        # 空の履歴を作成
        self.save_thread_history(thread_id, [])

        return thread_info

    def save_thread_info(self, thread_info):
        """スレッド情報を保存"""
        threads = self.list_threads()
        threads = [t for t in threads if t['id'] != thread_info['id']]
        threads.append(thread_info)

        with open(self.threads_file, 'w', encoding='utf-8') as f:
            json.dump(threads, f, ensure_ascii=False, indent=2)

    def list_threads(self):
        """全スレッド一覧を取得"""
        try:
            with open(self.threads_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def get_thread_history(self, thread_id):
        """特定のスレッドの履歴を取得"""
        try:
            with open(self._get_thread_file_path(thread_id), 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_thread_history(self, thread_id, history):
        """スレッドの履歴を保存"""
        file_path = self._get_thread_file_path(thread_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        # 最終更新日時を更新
        threads = self.list_threads()
        for thread in threads:
            if thread['id'] == thread_id:
                thread['updated_at'] = datetime.now().isoformat()
                self.save_thread_info(thread)
                break

    def update_thread_session_state(self, thread_id, session_state):
        """スレッドのセッション状態を更新"""
        threads = self.list_threads()
        for thread in threads:
            if thread['id'] == thread_id:
                thread['session_state'] = session_state
                self.save_thread_info(thread)
                break

    def get_thread_session_state(self, thread_id):
        """スレッドのセッション状態を取得"""
        threads = self.list_threads()
        for thread in threads:
            if thread['id'] == thread_id:
                return thread.get('session_state')
        return None

    def delete_thread(self, thread_id):
        """スレッドを削除"""
        # スレッド履歴ファイルを削除
        try:
            os.remove(self._get_thread_file_path(thread_id))
        except FileNotFoundError:
            pass

        # スレッド一覧から削除
        threads = self.list_threads()
        threads = [t for t in threads if t['id'] != thread_id]
        with open(self.threads_file, 'w', encoding='utf-8') as f:
            json.dump(threads, f, ensure_ascii=False, indent=2)

    def export_history(self, history, format='json'):
        """チャット履歴をエクスポート"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'format_version': '1.0',
                'history': history
            }

            if format == 'json':
                return json.dumps(export_data, ensure_ascii=False, indent=2)
            elif format == 'base64':
                json_str = json.dumps(export_data, ensure_ascii=False)
                return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            print(f"Error exporting chat history: {e}")
            return None

    def import_history(self, import_data, format='json'):
        """チャット履歴をインポート"""
        try:
            if format == 'json':
                if isinstance(import_data, str):
                    data = json.loads(import_data)
                else:
                    data = import_data
            elif format == 'base64':
                decoded_data = base64.b64decode(import_data.encode('utf-8')).decode('utf-8')
                data = json.loads(decoded_data)
            else:
                raise ValueError(f"Unsupported format: {format}")

            if 'format_version' not in data:
                raise ValueError("Invalid import data: missing format version")

            return data.get('history', [])
        except Exception as e:
            print(f"Error importing chat history: {e}")
            return None
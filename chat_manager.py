import json
from datetime import datetime
import base64
import os

class ChatManager:
    def __init__(self):
        self.history_file = "chat_history.json"
    
    def save_history(self, history):
        """Save chat history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'history': history
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving chat history: {e}")
            return False
    
    def load_history(self):
        """Load chat history from file"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('history', [])
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return []
    
    def clear_history(self):
        """Clear chat history"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({'timestamp': datetime.now().isoformat(), 'history': []}, f)
            return True
        except Exception as e:
            print(f"Error clearing chat history: {e}")
            return False

    def export_history(self, history, format='json'):
        """Export chat history to specified format"""
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
        """Import chat history from specified format"""
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

            # バージョンチェック
            if 'format_version' not in data:
                raise ValueError("Invalid import data: missing format version")

            return data.get('history', [])
        except Exception as e:
            print(f"Error importing chat history: {e}")
            return None
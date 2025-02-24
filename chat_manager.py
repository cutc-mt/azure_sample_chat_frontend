import json
from datetime import datetime

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

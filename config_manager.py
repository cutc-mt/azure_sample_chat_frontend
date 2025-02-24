import json
from pathlib import Path

class ConfigManager:
    CONFIG_FILE = "config.json"

    @staticmethod
    def get_default_config():
        return {
            'proxy_url': '',
            'api_endpoint': 'http://localhost:8000/chat',  # モックサーバーのエンドポイント
            'retrieval_mode': 'hybrid',
            'top_k': 5,
            'temperature': 0.7,
            'semantic_ranker': True,
            'semantic_captions': True,
            'followup_questions': True
        }

    @staticmethod
    def load_config():
        try:
            with open(ConfigManager.CONFIG_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            default_config = ConfigManager.get_default_config()
            ConfigManager.save_config(default_config)
            return default_config

    @staticmethod
    def save_config(config):
        with open(ConfigManager.CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

    @staticmethod
    def validate_config(config):
        required_fields = ['proxy_url', 'api_endpoint']
        for field in required_fields:
            if not config.get(field):
                return False, f"Missing required field: {field}"
        return True, "Configuration is valid"
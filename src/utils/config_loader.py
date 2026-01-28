"""
設定ファイル読み込みユーティリティ
"""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv


class ConfigLoader:
    """設定ファイルを読み込むクラス"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = config_path
        self.config = {}
        self._load_config()
        self._load_env()
    
    def _load_config(self):
        """YAML設定ファイルを読み込む"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def _load_env(self):
        """環境変数を読み込む"""
        load_dotenv()
        
        # API設定を環境変数から取得
        api_key = os.getenv('GMO_API_KEY')
        api_secret = os.getenv('GMO_API_SECRET')
        api_endpoint = os.getenv('GMO_API_ENDPOINT')
        
        if api_key:
            self.config['api']['key'] = api_key
        if api_secret:
            self.config['api']['secret'] = api_secret
        if api_endpoint:
            self.config['api']['endpoint'] = api_endpoint
    
    def get(self, key_path: str, default=None):
        """
        設定値を取得
        
        Args:
            key_path: ドット区切りのキーパス（例: 'api.endpoint'）
            default: デフォルト値
            
        Returns:
            設定値
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_api_key(self) -> str:
        """APIキーを取得"""
        return self.config.get('api', {}).get('key', '')
    
    def get_api_secret(self) -> str:
        """APIシークレットを取得"""
        return self.config.get('api', {}).get('secret', '')
    
    def get_api_endpoint(self) -> str:
        """APIエンドポイントを取得"""
        return self.config.get('api', {}).get('endpoint', 'https://api.coin.z.com')

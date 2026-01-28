"""
ConfigLoaderクラスのテスト
"""
import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open
from src.utils.config_loader import ConfigLoader


class TestConfigLoader:
    """ConfigLoaderクラスのテスト"""
    
    def test_init_with_valid_config(self):
        """有効な設定ファイルでの初期化テスト"""
        # 一時的な設定ファイルを作成
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "api": {
                    "endpoint": "https://api.coin.z.com"
                },
                "trading": {
                    "symbol": "BTC_JPY",
                    "amount": 0.001
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            config_path = str(config_file)
            loader = ConfigLoader(config_path=config_path)
            
            assert loader.config_path == config_path
            assert loader.config["api"]["endpoint"] == "https://api.coin.z.com"
            assert loader.config["trading"]["symbol"] == "BTC_JPY"
    
    def test_init_with_invalid_path(self):
        """存在しない設定ファイルでの初期化テスト"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader(config_path="nonexistent/config.yaml")
    
    def test_get_simple_value(self):
        """単純な設定値取得テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "api": {
                    "endpoint": "https://api.coin.z.com"
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(config_path=str(config_file))
            
            value = loader.get("api.endpoint")
            assert value == "https://api.coin.z.com"
    
    def test_get_nested_value(self):
        """ネストされた設定値取得テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "trading": {
                    "moving_average": {
                        "short_period": 20,
                        "long_period": 50
                    }
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(config_path=str(config_file))
            
            short_period = loader.get("trading.moving_average.short_period")
            assert short_period == 20
            
            long_period = loader.get("trading.moving_average.long_period")
            assert long_period == 50
    
    def test_get_with_default_value(self):
        """デフォルト値付き設定値取得テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "api": {
                    "endpoint": "https://api.coin.z.com"
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(config_path=str(config_file))
            
            # 存在しないキー
            value = loader.get("nonexistent.key", default="default_value")
            assert value == "default_value"
            
            # 存在するキー
            value = loader.get("api.endpoint", default="default_endpoint")
            assert value == "https://api.coin.z.com"
    
    def test_get_api_key(self):
        """APIキー取得テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "api": {
                    "key": "test_api_key_12345"
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(config_path=str(config_file))
            
            api_key = loader.get_api_key()
            assert api_key == "test_api_key_12345"
    
    def test_get_api_key_not_set(self):
        """APIキー未設定時のテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "api": {}
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(config_path=str(config_file))
            
            api_key = loader.get_api_key()
            assert api_key == ""
    
    def test_get_api_secret(self):
        """APIシークレット取得テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "api": {
                    "secret": "test_api_secret_67890"
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(config_path=str(config_file))
            
            api_secret = loader.get_api_secret()
            assert api_secret == "test_api_secret_67890"
    
    def test_get_api_secret_not_set(self):
        """APIシークレット未設定時のテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "api": {}
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(config_path=str(config_file))
            
            api_secret = loader.get_api_secret()
            assert api_secret == ""
    
    def test_get_api_endpoint(self):
        """APIエンドポイント取得テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "api": {
                    "endpoint": "https://custom.api.endpoint.com"
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(config_path=str(config_file))
            
            endpoint = loader.get_api_endpoint()
            assert endpoint == "https://custom.api.endpoint.com"
    
    def test_get_api_endpoint_default(self):
        """APIエンドポイント未設定時のデフォルト値テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "api": {}
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(config_path=str(config_file))
            
            endpoint = loader.get_api_endpoint()
            assert endpoint == "https://api.coin.z.com"
    
    @patch.dict(os.environ, {'GMO_API_KEY': 'env_api_key', 'GMO_API_SECRET': 'env_api_secret', 'GMO_API_ENDPOINT': 'https://env.endpoint.com'})
    def test_load_env_variables(self):
        """環境変数からの読み込みテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "api": {
                    "key": "config_api_key",
                    "secret": "config_api_secret",
                    "endpoint": "https://config.endpoint.com"
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(config_path=str(config_file))
            
            # 環境変数が優先される
            assert loader.get_api_key() == "env_api_key"
            assert loader.get_api_secret() == "env_api_secret"
            assert loader.get_api_endpoint() == "https://env.endpoint.com"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_load_env_variables_not_set(self):
        """環境変数未設定時のテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "api": {
                    "key": "config_api_key",
                    "secret": "config_api_secret",
                    "endpoint": "https://config.endpoint.com"
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(config_path=str(config_file))
            
            # 設定ファイルの値が使用される
            assert loader.get_api_key() == "config_api_key"
            assert loader.get_api_secret() == "config_api_secret"
            assert loader.get_api_endpoint() == "https://config.endpoint.com"
    
    def test_get_with_partial_path(self):
        """部分的なパスでの取得テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "trading": {
                    "symbol": "BTC_JPY",
                    "amount": 0.001
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(config_path=str(config_file))
            
            # 存在しない中間キー
            value = loader.get("trading.nonexistent.key", default="default")
            assert value == "default"
            
            # 存在するキー
            value = loader.get("trading.symbol", default="ETH_JPY")
            assert value == "BTC_JPY"

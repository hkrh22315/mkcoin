"""
GMOClientクラスのテスト
"""
import pytest
import time
import hmac
import hashlib
from unittest.mock import Mock, patch, MagicMock
from src.api.gmo_client import GMOClient


class TestGMOClient:
    """GMOClientクラスのテスト"""
    
    def test_init(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """初期化テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        assert client.api_key == mock_api_key
        assert client.api_secret == mock_api_secret
        assert client.endpoint == mock_api_endpoint
        assert client.public_endpoint == f"{mock_api_endpoint}/public"
        assert client.private_endpoint == f"{mock_api_endpoint}/private"
        assert client.consecutive_errors == 0
    
    def test_init_default_endpoint(self, mock_api_key, mock_api_secret):
        """デフォルトエンドポイントでの初期化テスト"""
        client = GMOClient(mock_api_key, mock_api_secret)
        
        assert client.endpoint == "https://api.coin.z.com"
        assert client.public_endpoint == "https://api.coin.z.com/public"
        assert client.private_endpoint == "https://api.coin.z.com/private"
    
    def test_get_timestamp(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """タイムスタンプ取得テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        timestamp = client._get_timestamp()
        
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
        
        # 現在時刻のミリ秒タイムスタンプと比較（±5秒の許容範囲）
        current_ms = int(time.time() * 1000)
        timestamp_int = int(timestamp)
        assert abs(timestamp_int - current_ms) < 5000
    
    def test_generate_signature(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """署名生成テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        timestamp = "1234567890"
        method = "GET"
        path = "/v1/account/assets"
        body = ""
        
        signature = client._generate_signature(timestamp, method, path, body)
        
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256のhex文字列は64文字
        
        # 期待される署名を計算
        text = timestamp + method + path + body
        expected_signature = hmac.new(
            mock_api_secret.encode('ascii'),
            text.encode('ascii'),
            hashlib.sha256
        ).hexdigest()
        
        assert signature == expected_signature
    
    def test_generate_signature_with_body(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """ボディ付き署名生成テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        timestamp = "1234567890"
        method = "POST"
        path = "/v1/order"
        body = '{"symbol":"BTC_JPY","side":"BUY","size":"0.01"}'
        
        signature = client._generate_signature(timestamp, method, path, body)
        
        assert isinstance(signature, str)
        assert len(signature) == 64
        
        # 期待される署名を計算
        text = timestamp + method + path + body
        expected_signature = hmac.new(
            mock_api_secret.encode('ascii'),
            text.encode('ascii'),
            hashlib.sha256
        ).hexdigest()
        
        assert signature == expected_signature
    
    @patch('src.api.gmo_client.requests.get')
    def test_get_status_success(self, mock_get, mock_api_key, mock_api_secret, mock_api_endpoint):
        """取引所ステータス取得テスト（成功）"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": 0,
            "data": {
                "status": "OPEN"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client.get_status()
        
        assert result["status"] == 0
        assert result["data"]["status"] == "OPEN"
        mock_get.assert_called_once()
    
    @patch('src.api.gmo_client.requests.get')
    def test_get_ticker_success(self, mock_get, mock_api_key, mock_api_secret, mock_api_endpoint):
        """Ticker取得テスト（成功）"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": 0,
            "data": [{
                "last": "5000000",
                "bid": "4999000",
                "ask": "5001000"
            }]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client.get_ticker("BTC_JPY")
        
        assert result["status"] == 0
        assert len(result["data"]) > 0
        mock_get.assert_called_once()
    
    @patch('src.api.gmo_client.requests.get')
    def test_get_ticker_without_symbol(self, mock_get, mock_api_key, mock_api_secret, mock_api_endpoint):
        """Ticker取得テスト（シンボル指定なし）"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": 0,
            "data": []
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client.get_ticker()
        
        assert result["status"] == 0
        mock_get.assert_called_once()
    
    @patch('src.api.gmo_client.requests.get')
    def test_get_orderbooks(self, mock_get, mock_api_key, mock_api_secret, mock_api_endpoint):
        """板情報取得テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": 0,
            "data": {
                "asks": [],
                "bids": []
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client.get_orderbooks("BTC_JPY")
        
        assert result["status"] == 0
        mock_get.assert_called_once()
    
    @patch('src.api.gmo_client.requests.get')
    def test_get_klines(self, mock_get, mock_api_key, mock_api_secret, mock_api_endpoint):
        """KLine情報取得テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": 0,
            "data": []
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client.get_klines("BTC_JPY", "5min", "20240101")
        
        assert result["status"] == 0
        mock_get.assert_called_once()
    
    @patch('src.api.gmo_client.requests.get')
    def test_get_assets(self, mock_get, mock_api_key, mock_api_secret, mock_api_endpoint):
        """資産残高取得テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": 0,
            "data": []
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client.get_assets()
        
        assert result["status"] == 0
        mock_get.assert_called_once()
        
        # プライベートAPIなので、ヘッダーが設定されていることを確認
        call_args = mock_get.call_args
        assert "API-KEY" in call_args.kwargs["headers"]
        assert "API-TIMESTAMP" in call_args.kwargs["headers"]
        assert "API-SIGN" in call_args.kwargs["headers"]
    
    @patch('src.api.gmo_client.requests.post')
    def test_place_order_market(self, mock_post, mock_api_key, mock_api_secret, mock_api_endpoint):
        """成行注文発注テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": 0,
            "data": 12345
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = client.place_order(
            symbol="BTC_JPY",
            side="BUY",
            execution_type="MARKET",
            size="0.01"
        )
        
        assert result["status"] == 0
        assert result["data"] == 12345
        mock_post.assert_called_once()
        
        # リクエストボディを確認
        call_args = mock_post.call_args
        assert call_args.kwargs["json"]["symbol"] == "BTC_JPY"
        assert call_args.kwargs["json"]["side"] == "BUY"
        assert call_args.kwargs["json"]["executionType"] == "MARKET"
        assert call_args.kwargs["json"]["size"] == "0.01"
    
    @patch('src.api.gmo_client.requests.post')
    def test_place_order_limit(self, mock_post, mock_api_key, mock_api_secret, mock_api_endpoint):
        """指値注文発注テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": 0,
            "data": 12346
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = client.place_order(
            symbol="BTC_JPY",
            side="SELL",
            execution_type="LIMIT",
            size="0.01",
            price="5000000"
        )
        
        assert result["status"] == 0
        mock_post.assert_called_once()
        
        # リクエストボディを確認
        call_args = mock_post.call_args
        assert call_args.kwargs["json"]["price"] == "5000000"
    
    @patch('src.api.gmo_client.requests.post')
    def test_cancel_order(self, mock_post, mock_api_key, mock_api_secret, mock_api_endpoint):
        """注文キャンセルテスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": 0,
            "data": {}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = client.cancel_order(order_id=12345)
        
        assert result["status"] == 0
        mock_post.assert_called_once()
        
        # リクエストボディを確認
        call_args = mock_post.call_args
        assert call_args.kwargs["json"]["orderId"] == 12345
    
    @patch('src.api.gmo_client.requests.get')
    def test_get_open_positions(self, mock_get, mock_api_key, mock_api_secret, mock_api_endpoint):
        """建玉一覧取得テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": 0,
            "data": {
                "list": []
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client.get_open_positions("BTC_JPY")
        
        assert result["status"] == 0
        mock_get.assert_called_once()
    
    @patch('src.api.gmo_client.requests.get')
    def test_api_error_status_not_zero(self, mock_get, mock_api_key, mock_api_secret, mock_api_endpoint):
        """APIエラーテスト（status != 0）"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": 1,
            "messages": [{
                "message_code": "ERR-5001",
                "message_string": "Invalid request"
            }]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception, match="API Error"):
            client.get_status()
    
    @patch('src.api.gmo_client.requests.get')
    def test_api_request_exception(self, mock_get, mock_api_key, mock_api_secret, mock_api_endpoint):
        """APIリクエスト例外テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        with pytest.raises(requests.exceptions.RequestException):
            client.get_status()
        
        # 連続エラーカウントが増えていることを確認
        assert client.consecutive_errors == 1
    
    @patch('src.api.gmo_client.requests.get')
    def test_consecutive_errors_reset_on_success(self, mock_get, mock_api_key, mock_api_secret, mock_api_endpoint):
        """成功時に連続エラーカウントがリセットされるテスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        
        # エラーを発生させる
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        try:
            client.get_status()
        except:
            pass
        
        assert client.consecutive_errors == 1
        
        # 成功するリクエスト
        mock_response = Mock()
        mock_response.json.return_value = {"status": 0, "data": {}}
        mock_response.raise_for_status = Mock()
        mock_get.side_effect = None
        mock_get.return_value = mock_response
        
        client.get_status()
        
        # エラーカウントがリセットされていることを確認
        assert client.consecutive_errors == 0

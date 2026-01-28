"""
GMOコインAPIクライアント
"""
import json
import time
import hmac
import hashlib
import requests
from typing import Dict, Optional, Any
from src.utils.logger import Logger


class GMOClient:
    """GMOコインAPIクライアントクラス"""
    
    def __init__(self, api_key: str, api_secret: str, endpoint: str = "https://api.coin.z.com"):
        """
        初期化
        
        Args:
            api_key: APIキー
            api_secret: APIシークレットキー
            endpoint: APIエンドポイント
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.endpoint = endpoint
        self.public_endpoint = f"{endpoint}/public"
        self.private_endpoint = f"{endpoint}/private"
        self.logger = Logger("gmo_client").get_logger()
        self.consecutive_errors = 0  # 連続エラーカウント
    
    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """
        署名を生成
        
        Args:
            timestamp: Unixタイムスタンプ（ミリ秒）
            method: HTTPメソッド
            path: リクエストパス
            body: リクエストボディ（JSON文字列）
            
        Returns:
            署名（hex文字列）
        """
        text = timestamp + method + path + body
        signature = hmac.new(
            self.api_secret.encode('ascii'),
            text.encode('ascii'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_timestamp(self) -> str:
        """
        現在時刻のUnixタイムスタンプ（ミリ秒）を取得
        
        Returns:
            タイムスタンプ文字列
        """
        return str(int(time.time() * 1000))
    
    def _make_private_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        body: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Private APIリクエストを送信
        
        Args:
            method: HTTPメソッド
            path: リクエストパス
            params: クエリパラメータ
            body: リクエストボディ
            
        Returns:
            APIレスポンス
            
        Raises:
            Exception: APIエラーが発生した場合
        """
        timestamp = self._get_timestamp()
        body_str = json.dumps(body) if body else ""
        signature = self._generate_signature(timestamp, method, path, body_str)
        
        headers = {
            "API-KEY": self.api_key,
            "API-TIMESTAMP": timestamp,
            "API-SIGN": signature,
            "Content-Type": "application/json"
        }
        
        url = f"{self.private_endpoint}{path}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=body, params=params, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=body, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, json=body, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            # エラーカウントをリセット
            self.consecutive_errors = 0
            
            # statusが0でない場合はエラー
            if result.get("status") != 0:
                error_msg = result.get("messages", [{}])[0].get("message_code", "Unknown error")
                raise Exception(f"API Error: {error_msg}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.consecutive_errors += 1
            self.logger.error(f"API request failed: {e}")
            raise
        except Exception as e:
            self.consecutive_errors += 1
            self.logger.error(f"Unexpected error: {e}")
            raise
    
    def _make_public_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Public APIリクエストを送信
        
        Args:
            method: HTTPメソッド
            path: リクエストパス
            params: クエリパラメータ
            
        Returns:
            APIレスポンス
        """
        url = f"{self.public_endpoint}{path}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") != 0:
                error_msg = result.get("messages", [{}])[0].get("message_code", "Unknown error")
                raise Exception(f"API Error: {error_msg}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Public API request failed: {e}")
            raise
    
    # Public API methods
    def get_status(self) -> Dict[str, Any]:
        """取引所ステータスを取得"""
        return self._make_public_request("GET", "/v1/status")
    
    def get_ticker(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        最新レートを取得
        
        Args:
            symbol: 銘柄（指定しない場合は全銘柄）
        """
        params = {"symbol": symbol} if symbol else None
        return self._make_public_request("GET", "/v1/ticker", params)
    
    def get_orderbooks(self, symbol: str) -> Dict[str, Any]:
        """
        板情報を取得
        
        Args:
            symbol: 銘柄
        """
        params = {"symbol": symbol}
        return self._make_public_request("GET", "/v1/orderbooks", params)
    
    def get_trades(self, symbol: str, page: int = 1, count: int = 100) -> Dict[str, Any]:
        """
        取引履歴を取得
        
        Args:
            symbol: 銘柄
            page: ページ番号
            count: 1ページあたりの件数
        """
        params = {"symbol": symbol, "page": page, "count": count}
        return self._make_public_request("GET", "/v1/trades", params)
    
    def get_klines(self, symbol: str, interval: str, date: str) -> Dict[str, Any]:
        """
        KLine情報（ローソク足）を取得
        
        Args:
            symbol: 銘柄
            interval: 時間足（1min, 5min, 15min, 30min, 1hour, 4hour, 8hour, 12hour, 1day, 1week, 1month）
            date: 日付（YYYYMMDD または YYYY）
        """
        params = {"symbol": symbol, "interval": interval, "date": date}
        return self._make_public_request("GET", "/v1/klines", params)
    
    # Private API methods
    def get_assets(self) -> Dict[str, Any]:
        """資産残高を取得"""
        return self._make_private_request("GET", "/v1/account/assets")
    
    def get_margin(self) -> Dict[str, Any]:
        """余力情報を取得"""
        return self._make_private_request("GET", "/v1/account/margin")
    
    def get_active_orders(self, symbol: str, page: int = 1, count: int = 100) -> Dict[str, Any]:
        """
        有効注文一覧を取得
        
        Args:
            symbol: 銘柄
            page: ページ番号
            count: 1ページあたりの件数
        """
        params = {"symbol": symbol, "page": page, "count": count}
        return self._make_private_request("GET", "/v1/activeOrders", params)
    
    def get_open_positions(self, symbol: str, page: int = 1, count: int = 100) -> Dict[str, Any]:
        """
        建玉一覧を取得（レバレッジ取引）
        
        Args:
            symbol: 銘柄
            page: ページ番号
            count: 1ページあたりの件数
        """
        params = {"symbol": symbol, "page": page, "count": count}
        return self._make_private_request("GET", "/v1/openPositions", params)
    
    def place_order(
        self,
        symbol: str,
        side: str,
        execution_type: str,
        size: str,
        price: Optional[str] = None,
        time_in_force: Optional[str] = None,
        losscut_price: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        注文を発注
        
        Args:
            symbol: 銘柄
            side: 売買区分（BUY/SELL）
            execution_type: 注文タイプ（MARKET/LIMIT/STOP）
            size: 注文数量
            price: 注文価格（LIMIT/STOPの場合は必須）
            time_in_force: 執行数量条件（FAK/FAS/FOK/SOK）
            losscut_price: ロスカットレート（レバレッジ取引のみ）
        """
        body = {
            "symbol": symbol,
            "side": side,
            "executionType": execution_type,
            "size": size
        }
        
        if price:
            body["price"] = price
        if time_in_force:
            body["timeInForce"] = time_in_force
        if losscut_price:
            body["losscutPrice"] = losscut_price
        
        return self._make_private_request("POST", "/v1/order", body=body)
    
    def cancel_order(self, order_id: int) -> Dict[str, Any]:
        """
        注文をキャンセル
        
        Args:
            order_id: 注文ID
        """
        body = {"orderId": order_id}
        return self._make_private_request("POST", "/v1/cancelOrder", body=body)
    
    def get_orders(self, order_ids: str) -> Dict[str, Any]:
        """
        注文情報を取得
        
        Args:
            order_ids: 注文ID（カンマ区切り、最大10件）
        """
        params = {"orderId": order_ids}
        return self._make_private_request("GET", "/v1/orders", params)
    
    def get_latest_executions(self, symbol: str, page: int = 1, count: int = 100) -> Dict[str, Any]:
        """
        最新約定一覧を取得
        
        Args:
            symbol: 銘柄
            page: ページ番号
            count: 1ページあたりの件数
        """
        params = {"symbol": symbol, "page": page, "count": count}
        return self._make_private_request("GET", "/v1/latestExecutions", params)

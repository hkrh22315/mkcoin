"""
RiskManagerクラスのテスト
"""
import pytest
from unittest.mock import Mock, MagicMock
from src.risk.risk_manager import RiskManager
from src.api.gmo_client import GMOClient


class TestRiskManager:
    """RiskManagerクラスのテスト"""
    
    def test_init(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """初期化テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        risk_manager = RiskManager(
            client,
            symbol="BTC_JPY",
            stop_loss=10000,
            take_profit=20000,
            max_position_size=0.01,
            max_reversal_count=5,
            max_consecutive_errors=3
        )
        
        assert risk_manager.symbol == "BTC_JPY"
        assert risk_manager.stop_loss == 10000
        assert risk_manager.take_profit == 20000
        assert risk_manager.max_position_size == 0.01
        assert risk_manager.max_reversal_count == 5
        assert risk_manager.max_consecutive_errors == 3
        assert risk_manager.reversal_count == 0
        assert risk_manager.last_order_side is None
    
    def test_check_stop_loss_buy_position(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """買いポジションの損切りチェックテスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        risk_manager = RiskManager(
            client,
            symbol="BTC_JPY",
            stop_loss=10000,
            take_profit=20000
        )
        
        # エントリー価格500万円、現在価格490万円、サイズ0.01BTC
        # 損失 = (5000000 - 4900000) * 0.01 = 10000円
        entry_price = 5000000
        current_price = 4900000
        size = 0.01
        
        # 損切り条件を満たす場合
        result = risk_manager.check_stop_loss(current_price, entry_price, "BUY", size)
        assert result is True
        
        # 損切り条件を満たさない場合（損失が小さい）
        current_price = 4950000  # 損失5000円
        result = risk_manager.check_stop_loss(current_price, entry_price, "BUY", size)
        assert result is False
    
    def test_check_stop_loss_sell_position(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """売りポジションの損切りチェックテスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        risk_manager = RiskManager(
            client,
            symbol="BTC_JPY",
            stop_loss=10000,
            take_profit=20000
        )
        
        # エントリー価格500万円、現在価格510万円、サイズ0.01BTC
        # 損失 = (5100000 - 5000000) * 0.01 = 10000円
        entry_price = 5000000
        current_price = 5100000
        size = 0.01
        
        # 損切り条件を満たす場合
        result = risk_manager.check_stop_loss(current_price, entry_price, "SELL", size)
        assert result is True
        
        # 損切り条件を満たさない場合
        current_price = 5050000  # 損失5000円
        result = risk_manager.check_stop_loss(current_price, entry_price, "SELL", size)
        assert result is False
    
    def test_check_take_profit_buy_position(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """買いポジションの利確チェックテスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        risk_manager = RiskManager(
            client,
            symbol="BTC_JPY",
            stop_loss=10000,
            take_profit=20000
        )
        
        # エントリー価格500万円、現在価格520万円、サイズ0.01BTC
        # 利益 = (5200000 - 5000000) * 0.01 = 20000円
        entry_price = 5000000
        current_price = 5200000
        size = 0.01
        
        # 利確条件を満たす場合
        result = risk_manager.check_take_profit(current_price, entry_price, "BUY", size)
        assert result is True
        
        # 利確条件を満たさない場合
        current_price = 5100000  # 利益10000円
        result = risk_manager.check_take_profit(current_price, entry_price, "BUY", size)
        assert result is False
    
    def test_check_take_profit_sell_position(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """売りポジションの利確チェックテスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        risk_manager = RiskManager(
            client,
            symbol="BTC_JPY",
            stop_loss=10000,
            take_profit=20000
        )
        
        # エントリー価格500万円、現在価格480万円、サイズ0.01BTC
        # 利益 = (5000000 - 4800000) * 0.01 = 20000円
        entry_price = 5000000
        current_price = 4800000
        size = 0.01
        
        # 利確条件を満たす場合
        result = risk_manager.check_take_profit(current_price, entry_price, "SELL", size)
        assert result is True
        
        # 利確条件を満たさない場合
        current_price = 4900000  # 利益10000円
        result = risk_manager.check_take_profit(current_price, entry_price, "SELL", size)
        assert result is False
    
    def test_check_position_size(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """ポジションサイズチェックテスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        risk_manager = RiskManager(
            client,
            symbol="BTC_JPY",
            max_position_size=0.01
        )
        
        # 許容範囲内
        result = risk_manager.check_position_size(0.005)
        assert result is True
        
        result = risk_manager.check_position_size(0.01)
        assert result is True
        
        # 上限超過
        result = risk_manager.check_position_size(0.02)
        assert result is False
    
    def test_check_reversal_count(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """反転注文数チェックテスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        risk_manager = RiskManager(
            client,
            symbol="BTC_JPY",
            max_reversal_count=5
        )
        
        # 最初の注文（反転なし）
        result = risk_manager.check_reversal_count("BUY")
        assert result is True
        assert risk_manager.reversal_count == 0
        assert risk_manager.last_order_side == "BUY"
        
        # 同じ方向の注文（反転なし）
        result = risk_manager.check_reversal_count("BUY")
        assert result is True
        assert risk_manager.reversal_count == 0
        
        # 反転注文
        result = risk_manager.check_reversal_count("SELL")
        assert result is True
        assert risk_manager.reversal_count == 1
        assert risk_manager.last_order_side == "SELL"
        
        # さらに反転
        for i in range(4):
            risk_manager.check_reversal_count("BUY" if i % 2 == 0 else "SELL")
        
        # 上限に達する
        result = risk_manager.check_reversal_count("BUY")
        assert result is False
        assert risk_manager.reversal_count == 5
    
    def test_check_consecutive_errors(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """連続エラーチェックテスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        risk_manager = RiskManager(
            client,
            symbol="BTC_JPY",
            max_consecutive_errors=3
        )
        
        # エラーなし
        client.consecutive_errors = 0
        result = risk_manager.check_consecutive_errors()
        assert result is True
        
        # エラー2回（許容範囲内）
        client.consecutive_errors = 2
        result = risk_manager.check_consecutive_errors()
        assert result is True
        
        # エラー3回（上限）
        client.consecutive_errors = 3
        result = risk_manager.check_consecutive_errors()
        assert result is False
        
        # エラー4回（上限超過）
        client.consecutive_errors = 4
        result = risk_manager.check_consecutive_errors()
        assert result is False
    
    def test_get_current_positions(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """現在のポジション取得テスト"""
        client = Mock(spec=GMOClient)
        risk_manager = RiskManager(
            client,
            symbol="BTC_JPY"
        )
        
        # モックのレスポンス
        mock_positions = [
            {
                "positionId": 12345,
                "side": "BUY",
                "size": "0.01",
                "price": "5000000"
            }
        ]
        client.get_open_positions.return_value = {
            "data": {"list": mock_positions}
        }
        
        positions = risk_manager.get_current_positions()
        assert len(positions) == 1
        assert positions[0]["positionId"] == 12345
        client.get_open_positions.assert_called_once_with("BTC_JPY")
    
    def test_record_trade(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """取引記録テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        risk_manager = RiskManager(
            client,
            symbol="BTC_JPY"
        )
        
        assert len(risk_manager.trade_history) == 0
        
        risk_manager.record_trade("BUY", 0.01, 5000000, order_id=12345)
        
        assert len(risk_manager.trade_history) == 1
        trade = risk_manager.trade_history[0]
        assert trade["side"] == "BUY"
        assert trade["size"] == 0.01
        assert trade["price"] == 5000000
        assert trade["order_id"] == 12345
    
    def test_reset_reversal_count(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """反転注文数リセットテスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        risk_manager = RiskManager(
            client,
            symbol="BTC_JPY"
        )
        
        # 反転回数を増やす
        risk_manager.check_reversal_count("BUY")
        risk_manager.check_reversal_count("SELL")
        assert risk_manager.reversal_count == 1
        
        # リセット
        risk_manager.reset_reversal_count()
        assert risk_manager.reversal_count == 0

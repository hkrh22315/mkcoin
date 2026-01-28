"""
MovingAverageStrategyクラスのテスト
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.strategy.moving_average import MovingAverageStrategy
from src.api.gmo_client import GMOClient


class TestMovingAverageStrategy:
    """MovingAverageStrategyクラスのテスト"""
    
    def test_init(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """初期化テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        strategy = MovingAverageStrategy(
            client,
            symbol="BTC_JPY",
            short_period=20,
            long_period=50,
            timeframe="5min"
        )
        
        assert strategy.symbol == "BTC_JPY"
        assert strategy.short_period == 20
        assert strategy.long_period == 50
        assert strategy.timeframe == "5min"
        assert strategy.last_signal is None
    
    def test_calculate_moving_averages_sufficient_data(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """移動平均線計算テスト（データ十分な場合）"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        strategy = MovingAverageStrategy(
            client,
            symbol="BTC_JPY",
            short_period=5,
            long_period=10
        )
        
        # サンプルデータを作成
        data = {
            'close': [5000000 + i * 1000 for i in range(20)]
        }
        df = pd.DataFrame(data)
        
        short_ma, long_ma = strategy.calculate_moving_averages(df)
        
        assert short_ma is not None
        assert long_ma is not None
        assert isinstance(short_ma, float)
        assert isinstance(long_ma, float)
        
        # 短期移動平均は最後の5つの平均
        expected_short = np.mean(df['close'].values[-5:])
        assert abs(short_ma - expected_short) < 0.01
        
        # 長期移動平均は最後の10つの平均
        expected_long = np.mean(df['close'].values[-10:])
        assert abs(long_ma - expected_long) < 0.01
    
    def test_calculate_moving_averages_insufficient_data(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """移動平均線計算テスト（データ不足の場合）"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        strategy = MovingAverageStrategy(
            client,
            symbol="BTC_JPY",
            short_period=5,
            long_period=10
        )
        
        # データが不足している場合
        data = {
            'close': [5000000 + i * 1000 for i in range(5)]
        }
        df = pd.DataFrame(data)
        
        short_ma, long_ma = strategy.calculate_moving_averages(df)
        
        assert short_ma is None
        assert long_ma is None
    
    def test_calculate_moving_averages_empty_data(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """移動平均線計算テスト（空データの場合）"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        strategy = MovingAverageStrategy(
            client,
            symbol="BTC_JPY",
            short_period=5,
            long_period=10
        )
        
        df = pd.DataFrame()
        
        short_ma, long_ma = strategy.calculate_moving_averages(df)
        
        assert short_ma is None
        assert long_ma is None
    
    @patch('src.strategy.moving_average.MovingAverageStrategy._get_klines_data')
    def test_get_signal_golden_cross(self, mock_get_klines, mock_api_key, mock_api_secret, mock_api_endpoint):
        """ゴールデンクロス（買いシグナル）テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        strategy = MovingAverageStrategy(
            client,
            symbol="BTC_JPY",
            short_period=5,
            long_period=10
        )
        
        # ゴールデンクロスをシミュレートするデータ
        # 前回: 短期 < 長期、今回: 短期 > 長期
        closes = [4900000 + i * 10000 for i in range(20)]
        # 最後の5つを大きく上げてゴールデンクロスを発生させる
        closes[-5:] = [5100000 + i * 20000 for i in range(5)]
        
        data = {
            'close': closes,
            'open': closes,
            'high': [c + 1000 for c in closes],
            'low': [c - 1000 for c in closes],
            'volume': [1.0] * len(closes),
            'openTime': [i * 300000 for i in range(len(closes))]
        }
        df = pd.DataFrame(data)
        
        mock_get_klines.return_value = df
        
        signal = strategy.get_signal()
        
        assert signal == "BUY"
        assert strategy.last_signal == "BUY"
    
    @patch('src.strategy.moving_average.MovingAverageStrategy._get_klines_data')
    def test_get_signal_dead_cross(self, mock_get_klines, mock_api_key, mock_api_secret, mock_api_endpoint):
        """デッドクロス（売りシグナル）テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        strategy = MovingAverageStrategy(
            client,
            symbol="BTC_JPY",
            short_period=5,
            long_period=10
        )
        
        # デッドクロスをシミュレートするデータ
        # 前回: 短期 > 長期、今回: 短期 < 長期
        closes = [5100000 - i * 10000 for i in range(20)]
        # 最後の5つを大きく下げてデッドクロスを発生させる
        closes[-5:] = [4900000 - i * 20000 for i in range(5)]
        
        data = {
            'close': closes,
            'open': closes,
            'high': [c + 1000 for c in closes],
            'low': [c - 1000 for c in closes],
            'volume': [1.0] * len(closes),
            'openTime': [i * 300000 for i in range(len(closes))]
        }
        df = pd.DataFrame(data)
        
        mock_get_klines.return_value = df
        
        signal = strategy.get_signal()
        
        assert signal == "SELL"
        assert strategy.last_signal == "SELL"
    
    @patch('src.strategy.moving_average.MovingAverageStrategy._get_klines_data')
    def test_get_signal_no_cross(self, mock_get_klines, mock_api_key, mock_api_secret, mock_api_endpoint):
        """クロスなし（シグナルなし）テスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        strategy = MovingAverageStrategy(
            client,
            symbol="BTC_JPY",
            short_period=5,
            long_period=10
        )
        
        # クロスが発生しないデータ
        closes = [5000000 + i * 1000 for i in range(20)]
        
        data = {
            'close': closes,
            'open': closes,
            'high': [c + 1000 for c in closes],
            'low': [c - 1000 for c in closes],
            'volume': [1.0] * len(closes),
            'openTime': [i * 300000 for i in range(len(closes))]
        }
        df = pd.DataFrame(data)
        
        mock_get_klines.return_value = df
        
        signal = strategy.get_signal()
        
        assert signal is None
    
    @patch('src.strategy.moving_average.MovingAverageStrategy._get_klines_data')
    def test_get_signal_empty_data(self, mock_get_klines, mock_api_key, mock_api_secret, mock_api_endpoint):
        """空データの場合のテスト"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        strategy = MovingAverageStrategy(
            client,
            symbol="BTC_JPY",
            short_period=5,
            long_period=10
        )
        
        mock_get_klines.return_value = pd.DataFrame()
        
        signal = strategy.get_signal()
        
        assert signal is None
    
    def test_get_current_price_success(self, mock_api_key, mock_api_secret, mock_api_endpoint, sample_ticker_data):
        """現在価格取得テスト（成功）"""
        client = Mock(spec=GMOClient)
        strategy = MovingAverageStrategy(
            client,
            symbol="BTC_JPY"
        )
        
        client.get_ticker.return_value = sample_ticker_data
        
        price = strategy.get_current_price()
        
        assert price == 5000000.0
        client.get_ticker.assert_called_once_with("BTC_JPY")
    
    def test_get_current_price_failure(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """現在価格取得テスト（失敗）"""
        client = Mock(spec=GMOClient)
        strategy = MovingAverageStrategy(
            client,
            symbol="BTC_JPY"
        )
        
        # 空のレスポンス
        client.get_ticker.return_value = {"data": []}
        
        price = strategy.get_current_price()
        
        assert price is None
    
    def test_get_current_price_exception(self, mock_api_key, mock_api_secret, mock_api_endpoint):
        """現在価格取得テスト（例外発生）"""
        client = Mock(spec=GMOClient)
        strategy = MovingAverageStrategy(
            client,
            symbol="BTC_JPY"
        )
        
        client.get_ticker.side_effect = Exception("API Error")
        
        price = strategy.get_current_price()
        
        assert price is None
    
    @patch('src.strategy.moving_average.MovingAverageStrategy.client')
    def test_get_klines_data_success(self, mock_client, mock_api_key, mock_api_secret, mock_api_endpoint, sample_klines_data):
        """KLineデータ取得テスト（成功）"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        strategy = MovingAverageStrategy(
            client,
            symbol="BTC_JPY",
            timeframe="5min"
        )
        
        mock_client.get_klines.return_value = {"data": sample_klines_data}
        
        df = strategy._get_klines_data(count=100)
        
        assert not df.empty
        assert 'close' in df.columns
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
    
    @patch('src.strategy.moving_average.MovingAverageStrategy.client')
    def test_get_klines_data_empty(self, mock_client, mock_api_key, mock_api_secret, mock_api_endpoint):
        """KLineデータ取得テスト（空データ）"""
        client = GMOClient(mock_api_key, mock_api_secret, mock_api_endpoint)
        strategy = MovingAverageStrategy(
            client,
            symbol="BTC_JPY",
            timeframe="5min"
        )
        
        mock_client.get_klines.return_value = {"data": []}
        
        df = strategy._get_klines_data(count=100)
        
        assert df.empty

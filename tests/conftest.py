"""
pytest共通設定とフィクスチャ
"""
import sys
from pathlib import Path
import pytest

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_api_key():
    """モック用のAPIキー"""
    return "test_api_key_12345"


@pytest.fixture
def mock_api_secret():
    """モック用のAPIシークレット"""
    return "test_api_secret_67890"


@pytest.fixture
def mock_api_endpoint():
    """モック用のAPIエンドポイント"""
    return "https://api.coin.z.com"


@pytest.fixture
def sample_klines_data():
    """サンプルのKLineデータ"""
    import pandas as pd
    import numpy as np
    
    # 100本のサンプルローソク足データを生成
    base_price = 5000000  # 500万円
    dates = pd.date_range(start='2024-01-01', periods=100, freq='5min')
    
    data = []
    for i, date in enumerate(dates):
        price_change = np.random.uniform(-10000, 10000)
        open_price = base_price + price_change
        high_price = open_price + np.random.uniform(0, 5000)
        low_price = open_price - np.random.uniform(0, 5000)
        close_price = np.random.uniform(low_price, high_price)
        volume = np.random.uniform(0.1, 10.0)
        
        data.append({
            'openTime': int(date.timestamp() * 1000),
            'open': str(open_price),
            'high': str(high_price),
            'low': str(low_price),
            'close': str(close_price),
            'volume': str(volume)
        })
        base_price = close_price
    
    return data


@pytest.fixture
def sample_ticker_data():
    """サンプルのTickerデータ"""
    return {
        "data": [{
            "last": "5000000",
            "bid": "4999000",
            "ask": "5001000",
            "high": "5100000",
            "low": "4900000",
            "volume": "100.5",
            "timestamp": "20240101000000"
        }]
    }

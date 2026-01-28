"""
移動平均線クロス戦略
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from src.api.gmo_client import GMOClient
from src.utils.logger import Logger


class MovingAverageStrategy:
    """移動平均線クロス戦略クラス"""
    
    def __init__(
        self,
        client: GMOClient,
        symbol: str,
        short_period: int = 20,
        long_period: int = 50,
        timeframe: str = "5min"
    ):
        """
        初期化
        
        Args:
            client: GMOコインAPIクライアント
            symbol: 通貨ペア
            short_period: 短期移動平均線の期間
            long_period: 長期移動平均線の期間
            timeframe: ローソク足の時間足
        """
        self.client = client
        self.symbol = symbol
        self.short_period = short_period
        self.long_period = long_period
        self.timeframe = timeframe
        self.logger = Logger("moving_average").get_logger()
        self.last_signal = None  # 最後のシグナル（BUY/SELL/None）
    
    def _get_klines_data(self, count: int = 100) -> pd.DataFrame:
        """
        ローソク足データを取得
        
        Args:
            count: 取得するローソク足の本数
            
        Returns:
            ローソク足データのDataFrame
        """
        from datetime import datetime, timedelta
        
        # 日付を計算（今日の日付）
        today = datetime.now()
        date_str = today.strftime("%Y%m%d")
        
        try:
            # KLineデータを取得
            response = self.client.get_klines(self.symbol, self.timeframe, date_str)
            klines = response.get("data", [])
            
            if not klines:
                # 昨日のデータも試す
                yesterday = today - timedelta(days=1)
                date_str = yesterday.strftime("%Y%m%d")
                response = self.client.get_klines(self.symbol, self.timeframe, date_str)
                klines = response.get("data", [])
            
            if not klines:
                self.logger.warning("KLineデータが取得できませんでした")
                return pd.DataFrame()
            
            # DataFrameに変換
            df = pd.DataFrame(klines)
            
            # 必要な列を数値型に変換
            df['open'] = pd.to_numeric(df['open'], errors='coerce')
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            df['openTime'] = pd.to_numeric(df['openTime'], errors='coerce')
            
            # NaNを削除
            df = df.dropna(subset=['open', 'high', 'low', 'close', 'openTime'])
            
            # 時系列でソート
            df = df.sort_values('openTime').reset_index(drop=True)
            
            # 指定された本数に制限
            if len(df) > count:
                df = df.tail(count).reset_index(drop=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"KLineデータ取得エラー: {e}")
            return pd.DataFrame()
    
    def calculate_moving_averages(self, df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
        """
        移動平均線を計算
        
        Args:
            df: ローソク足データのDataFrame
            
        Returns:
            (短期移動平均, 長期移動平均)のタプル
        """
        if df.empty or len(df) < self.long_period:
            self.logger.warning(f"データが不足しています。必要: {self.long_period}本, 実際: {len(df)}本")
            return None, None
        
        # 終値を使用して移動平均を計算
        closes = df['close'].values
        
        short_ma = np.mean(closes[-self.short_period:])
        long_ma = np.mean(closes[-self.long_period:])
        
        return short_ma, long_ma
    
    def get_signal(self) -> Optional[str]:
        """
        取引シグナルを取得
        
        Returns:
            "BUY": 買いシグナル（ゴールデンクロス）
            "SELL": 売りシグナル（デッドクロス）
            None: シグナルなし
        """
        # ローソク足データを取得（長期期間+余裕を持って取得）
        df = self._get_klines_data(count=self.long_period + 20)
        
        if df.empty:
            self.logger.error("ローソク足データが取得できませんでした")
            return None
        
        # 移動平均線を計算
        short_ma, long_ma = self.calculate_moving_averages(df)
        
        if short_ma is None or long_ma is None:
            return None
        
        # 前回の移動平均線を計算（クロス判定のため）
        if len(df) >= self.long_period + 1:
            prev_short_ma = np.mean(df['close'].values[-(self.short_period+1):-1])
            prev_long_ma = np.mean(df['close'].values[-(self.long_period+1):-1])
        else:
            prev_short_ma = short_ma
            prev_long_ma = long_ma
        
        self.logger.info(
            f"移動平均線 - 短期: {short_ma:.3f}, 長期: {long_ma:.3f}, "
            f"前回短期: {prev_short_ma:.3f}, 前回長期: {prev_long_ma:.3f}"
        )
        
        # ゴールデンクロス（短期線が長期線を上抜け）
        if prev_short_ma <= prev_long_ma and short_ma > long_ma:
            self.logger.info("ゴールデンクロス検出: 買いシグナル")
            self.last_signal = "BUY"
            return "BUY"
        
        # デッドクロス（短期線が長期線を下抜け）
        elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
            self.logger.info("デッドクロス検出: 売りシグナル")
            self.last_signal = "SELL"
            return "SELL"
        
        # シグナルなし
        return None
    
    def get_current_price(self) -> Optional[float]:
        """
        現在の価格を取得
        
        Returns:
            現在の価格（終値）
        """
        try:
            response = self.client.get_ticker(self.symbol)
            data = response.get("data", [])
            
            if data and isinstance(data, list) and len(data) > 0:
                ticker = data[0] if isinstance(data[0], dict) else data
                last_price = ticker.get("last")
                if last_price:
                    return float(last_price)
            
            return None
            
        except Exception as e:
            self.logger.error(f"価格取得エラー: {e}")
            return None

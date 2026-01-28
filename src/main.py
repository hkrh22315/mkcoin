"""
GMOコイン BTC/JPY自動売買プログラム メインファイル
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import csv

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config_loader import ConfigLoader
from src.utils.logger import Logger
from src.api.gmo_client import GMOClient
from src.strategy.moving_average import MovingAverageStrategy
from src.risk.risk_manager import RiskManager


class TradingBot:
    """自動売買ボットクラス"""
    
    def __init__(self):
        """初期化"""
        # 設定を読み込み
        self.config = ConfigLoader()
        
        # ロガーを初期化
        log_level = self.config.get("logging.level", "INFO")
        log_dir = self.config.get("logging.log_dir", "logs")
        self.logger = Logger("trading_bot", log_dir, log_level).get_logger()
        
        # APIクライアントを初期化
        api_key = self.config.get_api_key()
        api_secret = self.config.get_api_secret()
        api_endpoint = self.config.get_api_endpoint()
        
        if not api_key or not api_secret:
            self.logger.error("APIキーまたはシークレットキーが設定されていません")
            raise ValueError("API credentials not configured")
        
        self.client = GMOClient(api_key, api_secret, api_endpoint)
        
        # 取引設定を取得
        trading_config = self.config.get("trading", {})
        symbol = trading_config.get("symbol", "BTC_JPY")
        ma_config = trading_config.get("moving_average", {})
        short_period = ma_config.get("short_period", 20)
        long_period = ma_config.get("long_period", 50)
        timeframe = ma_config.get("timeframe", "5min")
        
        # 戦略を初期化
        self.strategy = MovingAverageStrategy(
            self.client,
            symbol,
            short_period,
            long_period,
            timeframe
        )
        
        # リスク管理設定を取得
        risk_config = self.config.get("risk_management", {})
        self.risk_manager = RiskManager(
            self.client,
            symbol,
            stop_loss=risk_config.get("stop_loss", 10000),
            take_profit=risk_config.get("take_profit", 20000),
            max_position_size=risk_config.get("max_position_size", 0.01),
            max_reversal_count=risk_config.get("max_reversal_count", 5),
            max_consecutive_errors=risk_config.get("max_consecutive_errors", 3)
        )
        
        # 取引設定
        self.order_type = trading_config.get("order_type", "MARKET")
        self.amount = trading_config.get("amount", 0.001)
        
        # 取引履歴ファイルのパス
        trade_history_dir = self.config.get("logging.trade_history_dir", "data")
        Path(trade_history_dir).mkdir(parents=True, exist_ok=True)
        self.trade_history_file = Path(trade_history_dir) / f"trade_history_{datetime.now().strftime('%Y%m%d')}.csv"
        
        self.logger.info("自動売買ボットを初期化しました")
    
    def save_trade_history(self, trade_data: dict):
        """
        取引履歴をCSVファイルに保存
        
        Args:
            trade_data: 取引データ
        """
        file_exists = self.trade_history_file.exists()
        
        with open(self.trade_history_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = [
                'timestamp', 'side', 'size', 'price', 'order_id',
                'signal', 'status', 'error_message'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(trade_data)
    
    def close_position(self, position_id: str, side: str, size: float):
        """
        既存ポジションを決済する
        
        Args:
            position_id: 決済対象のポジションID
            side: 元のポジションの売買区分（BUY/SELL）
            size: 決済数量
        """
        try:
            # 決済は元のポジションと逆方向の注文を出す
            close_side = "SELL" if side == "BUY" else "BUY"
            
            current_price = self.strategy.get_current_price()
            if current_price is None:
                self.logger.error("決済時に現在価格が取得できませんでした")
                return
            
            response = self.strategy.client.place_order(
                symbol=self.strategy.symbol,
                side=close_side,
                execution_type="MARKET",
                size=str(size),
                price=None
            )
            
            order_id = response.get("data")
            
            self.logger.info(
                f"ポジションを決済しました: position_id={position_id}, "
                f"side={close_side}, size={size}, price={current_price:.0f}, "
                f"order_id={order_id}"
            )
            
            # 決済取引を履歴に記録
            trade_data = {
                'timestamp': datetime.now().isoformat(),
                'side': close_side,
                'size': size,
                'price': current_price,
                'order_id': order_id,
                'signal': 'AUTO_CLOSE',
                'status': 'CLOSED',
                'error_message': ''
            }
            self.save_trade_history(trade_data)
            self.risk_manager.record_trade(close_side, size, current_price, order_id)
        
        except Exception as e:
            self.logger.error(
                f"ポジション決済エラー: position_id={position_id}, error={e}"
            )
            
            trade_data = {
                'timestamp': datetime.now().isoformat(),
                'side': side,
                'size': size,
                'price': 0,
                'order_id': None,
                'signal': 'AUTO_CLOSE',
                'status': 'ERROR_CLOSE',
                'error_message': str(e)
            }
            self.save_trade_history(trade_data)
    
    def check_existing_positions(self):
        """既存のポジションをチェックし、損切り・利確を実行"""
        try:
            positions = self.risk_manager.get_current_positions()
            
            if not positions:
                return
            
            current_price = self.strategy.get_current_price()
            if current_price is None:
                self.logger.warning("現在価格が取得できませんでした")
                return
            
            for position in positions:
                position_id = position.get("positionId")
                side = position.get("side")
                size = float(position.get("size", 0))
                entry_price = float(position.get("price", 0))
                
                # 損切りチェック
                if self.risk_manager.check_stop_loss(current_price, entry_price, side, size):
                    self.logger.warning(f"損切りを実行: ポジションID {position_id}")
                    # 決済注文を発注
                    self.close_position(position_id, side, size)
                    continue
                
                # 利確チェック
                if self.risk_manager.check_take_profit(current_price, entry_price, side, size):
                    self.logger.info(f"利確を実行: ポジションID {position_id}")
                    # 決済注文を発注
                    self.close_position(position_id, side, size)
                    continue
                    
        except Exception as e:
            self.logger.error(f"ポジションチェックエラー: {e}")
    
    def execute_trade(self, signal: str):
        """
        取引を実行
        
        Args:
            signal: シグナル（BUY/SELL）
        """
        # エラーチェック
        if not self.risk_manager.check_consecutive_errors():
            self.logger.error("連続エラーが上限に達しました。プログラムを停止します。")
            sys.exit(1)
        
        # 反転注文数チェック
        if not self.risk_manager.check_reversal_count(signal):
            self.logger.error("反転注文数の上限に達しました。取引を一時停止します。")
            return
        
        # ポジションサイズチェック
        if not self.risk_manager.check_position_size(self.amount):
            self.logger.warning("ポジションサイズが上限を超えています。取引をスキップします。")
            return
        
        try:
            current_price = self.strategy.get_current_price()
            if current_price is None:
                self.logger.error("現在価格が取得できませんでした")
                return
            
            # 注文を発注
            if self.order_type == "MARKET":
                price = None
            else:  # LIMIT
                # 指値注文の場合は現在価格を使用（実際には戦略に応じて調整）
                price = str(int(current_price))
            
            response = self.strategy.client.place_order(
                symbol=self.strategy.symbol,
                side=signal,
                execution_type=self.order_type,
                size=str(self.amount),
                price=price
            )
            
            order_id = response.get("data")
            
            self.logger.info(
                f"注文を発注しました: {signal} {self.amount} @ "
                f"{current_price:.0f} (注文ID: {order_id})"
            )
            
            # 取引履歴を記録
            trade_data = {
                'timestamp': datetime.now().isoformat(),
                'side': signal,
                'size': self.amount,
                'price': current_price,
                'order_id': order_id,
                'signal': 'MOVING_AVERAGE_CROSS',
                'status': 'ORDERED',
                'error_message': ''
            }
            
            self.save_trade_history(trade_data)
            self.risk_manager.record_trade(signal, self.amount, current_price, order_id)
            
        except Exception as e:
            self.logger.error(f"取引実行エラー: {e}")
            
            # エラーを記録
            trade_data = {
                'timestamp': datetime.now().isoformat(),
                'side': signal,
                'size': self.amount,
                'price': 0,
                'order_id': None,
                'signal': 'MOVING_AVERAGE_CROSS',
                'status': 'ERROR',
                'error_message': str(e)
            }
            self.save_trade_history(trade_data)
    
    def run_once(self):
        """1回の実行（手動実行モード）"""
        self.logger.info("=" * 60)
        self.logger.info("取引ボットを実行します")
        self.logger.info("=" * 60)
        
        try:
            # 取引所ステータスを確認
            status_response = self.client.get_status()
            status = status_response.get("data", {}).get("status")
            
            if status != "OPEN":
                self.logger.warning(f"取引所が開いていません。ステータス: {status}")
                return
            
            self.logger.info("取引所は開いています")
            
            # 既存ポジションのチェック（損切り・利確）
            self.check_existing_positions()
            
            # 現在の価格を取得
            current_price = self.strategy.get_current_price()
            if current_price:
                self.logger.info(f"現在価格: {current_price:.0f}円")
            
            # シグナルを取得
            signal = self.strategy.get_signal()
            
            if signal:
                self.logger.info(f"シグナル検出: {signal}")
                self.execute_trade(signal)
            else:
                self.logger.info("シグナルなし")
            
            # 資産残高を表示
            try:
                assets_response = self.client.get_assets()
                assets = assets_response.get("data", [])
                
                self.logger.info("=" * 60)
                self.logger.info("資産残高:")
                for asset in assets:
                    symbol = asset.get("symbol", "")
                    amount = asset.get("amount", "0")
                    available = asset.get("available", "0")
                    self.logger.info(f"  {symbol}: 残高={amount}, 利用可能={available}")
                self.logger.info("=" * 60)
                
            except Exception as e:
                self.logger.error(f"資産残高取得エラー: {e}")
            
            self.logger.info("実行完了")
            
        except Exception as e:
            self.logger.exception(f"実行エラー: {e}")
            raise


def main():
    """メイン関数"""
    try:
        bot = TradingBot()
        bot.run_once()
        
    except KeyboardInterrupt:
        print("\nプログラムを中断しました")
        sys.exit(0)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

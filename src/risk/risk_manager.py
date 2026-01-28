"""
リスク管理クラス
"""
from typing import Dict, Optional, List
from datetime import datetime
from src.api.gmo_client import GMOClient
from src.utils.logger import Logger


class RiskManager:
    """リスク管理クラス"""
    
    def __init__(
        self,
        client: GMOClient,
        symbol: str,
        stop_loss: float = 10000,
        take_profit: float = 20000,
        max_position_size: float = 0.01,
        max_reversal_count: int = 5,
        max_consecutive_errors: int = 3
    ):
        """
        初期化
        
        Args:
            client: GMOコインAPIクライアント
            symbol: 通貨ペア
            stop_loss: 損切り額（円）
            take_profit: 利確額（円）
            max_position_size: 最大ポジションサイズ（BTC単位）
            max_reversal_count: 反転注文数の上限
            max_consecutive_errors: エラー連続許容回数
        """
        self.client = client
        self.symbol = symbol
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.max_position_size = max_position_size
        self.max_reversal_count = max_reversal_count
        self.max_consecutive_errors = max_consecutive_errors
        
        self.logger = Logger("risk_manager").get_logger()
        
        # 状態管理
        self.reversal_count = 0  # 現在の反転注文数
        self.last_order_side = None  # 最後の注文の売買区分
        self.positions = []  # 現在のポジション情報
        self.trade_history = []  # 取引履歴
    
    def check_stop_loss(self, current_price: float, entry_price: float, side: str, size: float) -> bool:
        """
        損切り条件をチェック
        
        Args:
            current_price: 現在の価格
            entry_price: エントリー価格
            side: 売買区分（BUY/SELL）
            size: ポジションサイズ
            
        Returns:
            True: 損切り条件を満たしている
        """
        if side == "BUY":
            # 買いポジションの場合、価格が下がったら損失
            loss = (entry_price - current_price) * size
        else:  # SELL
            # 売りポジションの場合、価格が上がったら損失
            loss = (current_price - entry_price) * size
        
        # 損失を円に変換（BTC/JPYの場合）
        loss_jpy = loss * current_price if side == "BUY" else loss * current_price
        
        if loss_jpy >= self.stop_loss:
            self.logger.warning(f"損切り条件を満たしました。損失: {loss_jpy:.0f}円")
            return True
        
        return False
    
    def check_take_profit(self, current_price: float, entry_price: float, side: str, size: float) -> bool:
        """
        利確条件をチェック
        
        Args:
            current_price: 現在の価格
            entry_price: エントリー価格
            side: 売買区分（BUY/SELL）
            size: ポジションサイズ
            
        Returns:
            True: 利確条件を満たしている
        """
        if side == "BUY":
            # 買いポジションの場合、価格が上がったら利益
            profit = (current_price - entry_price) * size
        else:  # SELL
            # 売りポジションの場合、価格が下がったら利益
            profit = (entry_price - current_price) * size
        
        # 利益を円に変換（BTC/JPYの場合）
        profit_jpy = profit * current_price if side == "BUY" else profit * current_price
        
        if profit_jpy >= self.take_profit:
            self.logger.info(f"利確条件を満たしました。利益: {profit_jpy:.0f}円")
            return True
        
        return False
    
    def check_position_size(self, size: float) -> bool:
        """
        ポジションサイズをチェック
        
        Args:
            size: 注文数量
            
        Returns:
            True: ポジションサイズが許容範囲内
        """
        if size > self.max_position_size:
            self.logger.warning(
                f"ポジションサイズが上限を超えています。"
                f"要求: {size}, 上限: {self.max_position_size}"
            )
            return False
        
        return True
    
    def check_reversal_count(self, side: str) -> bool:
        """
        反転注文数をチェック
        
        Args:
            side: 売買区分（BUY/SELL）
            
        Returns:
            True: 反転注文数の上限内
        """
        # 最後の注文と反転しているかチェック
        if self.last_order_side is not None and self.last_order_side != side:
            self.reversal_count += 1
            self.logger.info(f"反転注文を検出。現在の反転回数: {self.reversal_count}")
        else:
            # 同じ方向の注文の場合はリセット
            self.reversal_count = 0
        
        self.last_order_side = side
        
        if self.reversal_count >= self.max_reversal_count:
            self.logger.error(
                f"反転注文数の上限に達しました。"
                f"現在: {self.reversal_count}, 上限: {self.max_reversal_count}"
            )
            return False
        
        return True
    
    def check_consecutive_errors(self) -> bool:
        """
        連続エラー数をチェック
        
        Returns:
            True: エラー連続許容回数内
        """
        error_count = self.client.consecutive_errors
        
        if error_count >= self.max_consecutive_errors:
            self.logger.error(
                f"エラーが連続して発生しています。"
                f"現在: {error_count}, 上限: {self.max_consecutive_errors}"
            )
            return False
        
        return True
    
    def get_current_positions(self) -> List[Dict]:
        """
        現在のポジションを取得
        
        Returns:
            ポジション情報のリスト
        """
        try:
            # レバレッジ取引の建玉を取得
            response = self.client.get_open_positions(self.symbol)
            positions = response.get("data", {}).get("list", [])
            
            self.positions = positions
            return positions
            
        except Exception as e:
            self.logger.error(f"ポジション取得エラー: {e}")
            return []
    
    def record_trade(
        self,
        side: str,
        size: float,
        price: float,
        order_id: Optional[int] = None
    ):
        """
        取引を記録
        
        Args:
            side: 売買区分
            size: 数量
            price: 価格
            order_id: 注文ID
        """
        trade = {
            "timestamp": datetime.now().isoformat(),
            "side": side,
            "size": size,
            "price": price,
            "order_id": order_id
        }
        
        self.trade_history.append(trade)
        self.logger.info(f"取引を記録: {side} {size} @ {price}")
    
    def reset_reversal_count(self):
        """反転注文数をリセット"""
        self.reversal_count = 0
        self.logger.info("反転注文数をリセットしました")

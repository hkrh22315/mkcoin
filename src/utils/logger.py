"""
ログ機能ユーティリティ
"""
import logging
import os
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


class Logger:
    """ログ管理クラス"""
    
    def __init__(self, name: str = "mkcoin", log_dir: str = "logs", level: str = "INFO"):
        """
        初期化
        
        Args:
            name: ロガー名
            log_dir: ログディレクトリ
            level: ログレベル
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # ロガーの設定
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # 既存のハンドラーをクリア
        self.logger.handlers.clear()
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # ファイルハンドラー（ローテーション）
        log_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """ロガーインスタンスを取得"""
        return self.logger
    
    def debug(self, message: str):
        """DEBUGレベルのログを記録"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """INFOレベルのログを記録"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """WARNINGレベルのログを記録"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """ERRORレベルのログを記録"""
        self.logger.error(message)
    
    def exception(self, message: str):
        """例外情報を含むERRORレベルのログを記録"""
        self.logger.exception(message)

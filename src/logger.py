import logging
import sys
from pathlib import Path
from typing import Optional


class ScraperLogger:
    """Class for configuring logging"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger('quotes_scraper')
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logger"""
        log_config = self.config.get('logging', {})
        log_file = self.config['storage']['log_file']
        
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))
        
        formatter = logging.Formatter(
            log_config.get('format', '[%(asctime)s] %(levelname)s: %(message)s'),
            datefmt=log_config.get('date_format', '%Y-%m-%d %H:%M:%S')
        )
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def get_logger(self) -> logging.Logger:
        """Get configured logger"""
        return self.logger
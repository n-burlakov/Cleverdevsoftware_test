import json

from pathlib import Path
from typing import List, Dict, Any

from .logger import ScraperLogger


class DataStorage:
    """Class for working with file storage"""
    
    def __init__(self, config: dict, logger: ScraperLogger):
        self.config = config
        self.logger = logger.get_logger()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Creating necessary directories"""
        output_file = self.config['storage']['output_file']
        author_file = self.config['storage']['author_quotes_file']
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(author_file).parent.mkdir(parents=True, exist_ok=True)
    
    def save_quotes(self, quotes: List[Dict[str, Any]], filename: str = None) -> bool:
        """Saving quotes to a JSON file"""
        if not filename:
            filename = self.config['storage']['output_file']
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(quotes, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Data saved to {filename} ({len(quotes)} records)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving to {filename}: {str(e)}")
            return False
    
    def save_author_quotes(self, author: str, quotes: List[Dict[str, Any]]) -> bool:
        """Saving quotes of an author to a separate file"""
        filename = self.config['storage']['author_quotes_file']
        
        data = {
            'author': author,
            'total_quotes': len(quotes),
            'quotes': quotes
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Quotes of author {author} saved to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving quotes of author: {str(e)}")
            return False

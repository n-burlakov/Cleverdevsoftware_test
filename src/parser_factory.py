from typing import Optional

from .logger import ScraperLogger
from .parsers.base_parser import BaseParser
from .parsers.bs4_parser import BS4Parser
from .parsers.selenium_parser import SeleniumParser


class ParserFactory:
    """Factory class for creating parsers"""
    
    PARSER_TYPES = {
        'bs4': BS4Parser,
        'beautifulsoup': BS4Parser,
        'selenium': SeleniumParser,
    }
    
    @staticmethod
    def create_parser(parser_type: str, logger: Optional[ScraperLogger] = None) -> BaseParser:
        """
        Create parser instance based on type
        
        Args:
            parser_type: Type of parser ('bs4', 'beautifulsoup', or 'selenium')
            logger: Optional logger instance
            
        Returns:
            Parser instance
            
        Raises:
            ValueError: If parser type is not supported
        """
        parser_type_lower = parser_type.lower()
        
        if parser_type_lower not in ParserFactory.PARSER_TYPES:
            available = ', '.join(ParserFactory.PARSER_TYPES.keys())
            raise ValueError(
                f"Unsupported parser type: {parser_type}. "
                f"Available types: {available}"
            )
        
        parser_class = ParserFactory.PARSER_TYPES[parser_type_lower]
        
        if logger:
            logger_instance = logger.get_logger()
            logger_instance.info(f"Creating {parser_type_lower} parser")
        
        if parser_type_lower == 'selenium':
            return parser_class()
        else:
            return parser_class()

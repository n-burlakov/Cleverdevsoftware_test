"""Parser module for different parsing backends"""

from .base_parser import BaseParser
from .bs4_parser import BS4Parser
from .selenium_parser import SeleniumParser

__all__ = ['BaseParser', 'BS4Parser', 'SeleniumParser']


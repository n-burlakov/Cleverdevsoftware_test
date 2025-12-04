class ScraperException(Exception):
    """Basic exception for scraper"""
    pass

class AuthenticationError(ScraperException):
    """Authentication error"""
    pass

class ConfigurationError(ScraperException):
    """Configuration error"""
    pass

class NetworkError(ScraperException):
    """Network error"""
    pass

class ParsingError(ScraperException):
    """Parsing error"""
    pass

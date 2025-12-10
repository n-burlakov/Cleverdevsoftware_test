import asyncio
import json
import sys
from pathlib import Path

from src.cli import CommandLineInterface
from src.logger import ScraperLogger
from src.auth import Authenticator
from src.scraper import AsyncScraper
from src.storage import DataStorage
from src.exceptions import ConfigurationError


class QuotesScraperApp:
    """Main application class"""
    
    def __init__(self):
        self.config = None
        self.logger = None
        self.storage = None
    
    def load_config(self, config_path: str, cli_args) -> dict:
        """Loading and validating configuration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # сheck required top-level fields
            required_fields = ['auth', 'scraping', 'storage', 'logging']
            for field in required_fields:
                if field not in config:
                    raise ConfigurationError(f"Required field is missing: {field}")
            
            # validate auth section
            auth_required = ['login_url', 'username', 'password']
            for field in auth_required:
                if field not in config['auth']:
                    raise ConfigurationError(f"Required auth field is missing: {field}")
                # check that string fields are not empty
                if field in ['login_url', 'username', 'password']:
                    if not config['auth'][field] or not isinstance(config['auth'][field], str) or not config['auth'][field].strip():
                        raise ConfigurationError(f"Auth field '{field}' must be a non-empty string")
            
            # validate optional auth fields if present
            if 'retry_attempts' in config['auth']:
                if not isinstance(config['auth']['retry_attempts'], int) or config['auth']['retry_attempts'] <= 0:
                    raise ConfigurationError("auth.retry_attempts must be a positive integer")
            if 'retry_delay' in config['auth']:
                if not isinstance(config['auth']['retry_delay'], (int, float)) or config['auth']['retry_delay'] < 0:
                    raise ConfigurationError("auth.retry_delay must be a non-negative number")
            
            # validate scraping section
            scraping_required = ['base_url', 'max_pages', 'retry_attempts', 'retry_delay', 'timeout']
            for field in scraping_required:
                if field not in config['scraping']:
                    raise ConfigurationError(f"Required scraping field is missing: {field}")
            
            # validate scraping field values
            if not config['scraping']['base_url'] or not isinstance(config['scraping']['base_url'], str) or not config['scraping']['base_url'].strip():
                raise ConfigurationError("scraping.base_url must be a non-empty string")
            
            # max_pages can be null (for auto-discovery) or a positive integer
            if config['scraping']['max_pages'] is not None:
                if not isinstance(config['scraping']['max_pages'], int) or config['scraping']['max_pages'] <= 0:
                    raise ConfigurationError("scraping.max_pages must be null or a positive integer")
            
            if not isinstance(config['scraping']['retry_attempts'], int) or config['scraping']['retry_attempts'] <= 0:
                raise ConfigurationError("scraping.retry_attempts must be a positive integer")
            
            if not isinstance(config['scraping']['retry_delay'], (int, float)) or config['scraping']['retry_delay'] < 0:
                raise ConfigurationError("scraping.retry_delay must be a non-negative number")
            
            if not isinstance(config['scraping']['timeout'], (int, float)) or config['scraping']['timeout'] <= 0:
                raise ConfigurationError("scraping.timeout must be a positive number")
            
            # validate optional scraping fields if present
            if 'parser_type' in config['scraping']:
                if not isinstance(config['scraping']['parser_type'], str) or config['scraping']['parser_type'].strip() not in ['bs4', 'beautifulsoup', 'selenium']:
                    raise ConfigurationError("scraping.parser_type must be one of: 'bs4', 'beautifulsoup', 'selenium'")
            
            # validate storage section
            storage_required = ['output_file', 'author_quotes_file', 'log_file']
            for field in storage_required:
                if field not in config['storage']:
                    raise ConfigurationError(f"Required storage field is missing: {field}")
                # check that file paths are not empty
                if not config['storage'][field] or not isinstance(config['storage'][field], str) or not config['storage'][field].strip():
                    raise ConfigurationError(f"Storage field '{field}' must be a non-empty string")
            
            # validate logging section
            logging_required = ['level', 'format', 'date_format']
            for field in logging_required:
                if field not in config['logging']:
                    raise ConfigurationError(f"Required logging field is missing: {field}")
                # check that string fields are not empty
                if not config['logging'][field] or not isinstance(config['logging'][field], str) or not config['logging'][field].strip():
                    raise ConfigurationError(f"Logging field '{field}' must be a non-empty string")
            
            # validate logging level
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if config['logging']['level'].upper() not in valid_levels:
                raise ConfigurationError(f"logging.level must be one of: {', '.join(valid_levels)}")
            
            # validate cli arguments
            if cli_args.pages:
                if cli_args.pages <= 0:
                    raise ConfigurationError("Number of pages must be positive")
                config['scraping']['max_pages'] = cli_args.pages
            
            if cli_args.output:
                if not cli_args.output.endswith('.json'):
                    raise ConfigurationError("Output file must have .json extension")
                config['storage']['output_file'] = cli_args.output
            
            return config
            
        except json.JSONDecodeError as e:
            print(f"Error in configuration file format: {str(e)}")
            sys.exit(1)
        except ConfigurationError as e:
            print(f"Configuration error: {str(e)}")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            sys.exit(1)
    
    async def run(self):
        """Main method of application launch"""

        args = CommandLineInterface.parse_args()
        CommandLineInterface.validate_args(args)
        
        self.config = self.load_config(args.config, args)
        
        self.logger = ScraperLogger(self.config)
        logger_instance = self.logger.get_logger()
        
        self.storage = DataStorage(self.config, self.logger)
        
        logger_instance.info("Starting scraper for quotes.toscrape.com")
        
        if args.author:
            await self.search_author_quotes(args.author)
            return
        
        await self.full_scraping_process()
    
    async def search_author_quotes(self, author_name: str):
        """Search for quotes of a specific author"""
        logger = self.logger.get_logger()
        logger.info(f"Searching for quotes of author: {author_name}")
        
        if not await self._check_site_availability():
            logger.error("Site is not available. Please check your internet connection and try again.")
            print("\nError: Site is not available. Please check your internet connection.\n")
            return
        
        async with Authenticator(self.config, self.logger) as auth:
            if not await auth.login():
                logger.error("Failed to perform authentication")
                print("\nError: Authentication failed. Please check your credentials in config.json\n")
                return
            
            scraper = AsyncScraper(self.config, self.logger, auth.session)
            try:
                author_quotes = await scraper.scrape_author_quotes(author_name)
                
                if author_quotes:
                    print(f"\nFound {len(author_quotes)} quote(s) of author {author_name}:\n")
                    for i, quote in enumerate(author_quotes, 1):
                        print(f"{i}. {quote['text']}")
                        print(f"   Tags: {', '.join(quote['tags'])}\n")
                    
                    self.storage.save_author_quotes(author_name, author_quotes)
                    logger.info(f"Successfully found and saved {len(author_quotes)} quotes for author {author_name}")
                else:
                    logger.warning(f"Quotes of author {author_name} not found")
                    print(f"\nQuotes of author '{author_name}' not found\n")
            finally:
                await scraper.close()
    
    async def full_scraping_process(self):
        """Full scraping process with authentication"""
        logger = self.logger.get_logger()
        
        if not await self._check_site_availability():
            logger.error("Site is not available. Please check your internet connection and try again.")
            return
        
        async with Authenticator(self.config, self.logger) as auth:
            logger.info("Performing authentication...")
            if not await auth.login():
                logger.error("Failed to perform authentication")
                return
            
            logger.info("Starting data collection...")
            scraper = AsyncScraper(self.config, self.logger, auth.session)
            try:
                quotes = await scraper.scrape_random_pages()
                
                if quotes:
                    self.storage.save_quotes(quotes)
                    logger.info(f"Data collection completed. Total collected: {len(quotes)} quotes")
                else:
                    logger.warning("Failed to collect data")
            finally:
                await scraper.close()
        
        logger.info("Scraper work completed")
    
    async def _check_site_availability(self) -> bool:
        """Check if the site is available"""
        import aiohttp
        base_url = self.config['scraping']['base_url']
        timeout = aiohttp.ClientTimeout(total=5)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, timeout=timeout) as response:
                    return response.status == 200
        except asyncio.TimeoutError:
            if self.logger:
                self.logger.get_logger().error("Site availability check failed: timeout")
            return False
        except aiohttp.ClientError as e:
            if self.logger:
                self.logger.get_logger().error(f"Site availability check failed: network error - {str(e)}")
            return False
        except Exception as e:
            if self.logger:
                self.logger.get_logger().error(f"Site availability check failed: {str(e)}")
            return False


def main():
    """Entry point"""
    app = QuotesScraperApp()
    asyncio.run(app.run())


if __name__ == "__main__":
    main()

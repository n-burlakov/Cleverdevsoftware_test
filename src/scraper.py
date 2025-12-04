import aiohttp
import asyncio
import random
from typing import List, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from .parser_factory import ParserFactory
from .parsers.base_parser import BaseParser
from .exceptions import NetworkError
from .logger import ScraperLogger


class AsyncScraper:
    """Asynchronous scraper for collecting quotes"""
    
    def __init__(self, config: dict, logger: ScraperLogger, session: aiohttp.ClientSession):
        self.config = config
        self.logger = logger.get_logger()
        self.session = session
        self.base_url = config['scraping']['base_url']
        self.max_pages = config['scraping'].get('max_pages')
        self.retry_attempts = config['scraping']['retry_attempts']
        self.retry_delay = config['scraping']['retry_delay']
        timeout_value = config['scraping']['timeout']
        self.timeout = aiohttp.ClientTimeout(total=timeout_value)
        self.random_pages = config['scraping'].get('random_pages', True)
        
        parser_type = config['scraping'].get('parser_type', 'bs4')
        self.parser = ParserFactory.create_parser(parser_type, logger)
        self.parser_type = parser_type.lower()
    
    async def scrape_random_pages(self) -> List[Dict[str, any]]:
        """Collection of data from random pages"""
        all_quotes = []
        pages_to_scrape = await self._select_pages_to_scrape()
        
        self.logger.info(f"Starting collection of data from {len(pages_to_scrape)} pages")
        
        for page_num in pages_to_scrape:
            try:
                quotes = await self._scrape_page_with_retry(page_num)
                if quotes:
                    all_quotes.extend(quotes)
                    self.logger.info(f"Page {page_num}: collected {len(quotes)} quotes")
                else:
                    self.logger.warning(f"Page {page_num}: quotes not found")
            except Exception as e:
                self.logger.error(f"Error scraping page {page_num}: {str(e)}")
                continue
        
        self.logger.info(f"Total collected {len(all_quotes)} quotes")
        return all_quotes
    
    async def scrape_author_quotes(self, author_name: str) -> List[Dict[str, any]]:
        """Search for quotes of a specific author"""
        author_quotes = []
        
        self.logger.info(f"Author page not found, searching through all pages...")
        page_num = 1
        
        while True:
            if self.max_pages and page_num > self.max_pages:
                break
            
            try:
                if await self._has_no_quotes(page_num):
                    self.logger.info(f"Page {page_num}: No quotes found! Stopping pagination.")
                    break
                
                quotes = await self._scrape_page_with_retry(page_num)
                
                if not quotes:
                    if not await self._has_next_page(page_num):
                        break
                    page_num += 1
                    continue
                
                for quote in quotes:
                    if quote['author'].lower() == author_name.lower():
                        author_quotes.append(quote)
                
                if not await self._has_next_page(page_num):
                    break
                    
                page_num += 1
                
            except Exception as e:
                self.logger.error(f"Error searching for author on page {page_num}: {str(e)}")
                page_num += 1
                continue
        
        return author_quotes
    
    async def close(self):
        """Closing parser resources"""
        if hasattr(self, 'parser') and self.parser_type == 'selenium':
            try:
                if hasattr(self.parser, 'close'):
                    await asyncio.to_thread(self.parser.close)
                    self.logger.debug("Selenium parser closed successfully")
            except Exception as e:
                self.logger.debug(f"Error closing parser: {str(e)}")
    
    async def _select_pages_to_scrape(self) -> List[int]:
        """Selection of pages for scraping"""
        if not self.max_pages or self.max_pages == 0:
            return await self._discover_pages()
        
        if self.random_pages:
            pages = random.sample(range(1, self.max_pages + 1), self.max_pages)
            return sorted(pages)
        else:
            return list(range(1, self.max_pages + 1))
    
    async def _discover_pages(self) -> List[int]:
        """Discover all available pages by checking pagination until 'No quotes found!'"""
        pages = []
        page_num = 1
        
        self.logger.info("max_pages not set, discovering pages by checking pagination...")
        
        while True:
            try:
                
                if await self._has_no_quotes(page_num):
                    self.logger.info(f"Page {page_num}: No quotes found! Discovered {len(pages)} pages total.")
                    break
                
                pages.append(page_num)
                page_num += 1
                
            except Exception as e:
                self.logger.error(f"Error discovering page {page_num}: {str(e)}")
                break
        
        return pages
    
    async def _has_no_quotes(self, page_num: int) -> bool:
        """Check if page contains 'No quotes found!' message"""
        url = f"{self.base_url}/page/{page_num}/" if page_num > 1 else self.base_url + "/"
        
        if self.parser_type == 'selenium':
            from .parsers.selenium_parser import SeleniumParser
            if isinstance(self.parser, SeleniumParser):
                try:
                    def check_page():
                        driver = self.parser._get_driver()
                        driver.get(url)
                        return driver.page_source
                    
                    page_source = await asyncio.to_thread(check_page)
                    return self.parser.has_no_quotes(page_source)
                except Exception as e:
                    self.logger.debug(f"Error checking 'No quotes found!' with Selenium on page {page_num}: {str(e)}")
                    return False
        
        try:
            async with self.session.get(url, timeout=self.timeout) as response:
                if response.status == 200:
                    html = await response.text()
                    return self.parser.has_no_quotes(html)
                elif response.status == 404:
                    return True
        except Exception as e:
            self.logger.debug(f"Error checking 'No quotes found!' on page {page_num}: {str(e)}")
            return False
        
        return False
    
    async def _scrape_page_with_retry(self, page_num: int) -> List[Dict[str, any]]:
        """Scraping a page with a retry mechanism"""
        url = f"{self.base_url}/page/{page_num}/" if page_num > 1 else self.base_url + "/"
        
        if self.parser_type == 'selenium':
            return await self._scrape_page_with_selenium(url, page_num)
        
        for attempt in range(self.retry_attempts):
            try:
                async with self.session.get(url, timeout=self.timeout) as response:
                    if response.status == 200:
                        html = await response.text()
                        quotes = self.parser.parse_quotes_from_html(html)
                        return quotes
                    elif response.status == 404:
                        self.logger.warning(f"Page {page_num}: not found (404)")
                        return []
                    else:
                        self.logger.warning(f"Page {page_num}: status {response.status}, attempt {attempt + 1}")
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout loading page {page_num}, attempt {attempt + 1}/{self.retry_attempts}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                    
            except aiohttp.ClientError as e:
                self.logger.error(f"Network error loading page {page_num}, attempt {attempt + 1}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                    
            except Exception as e:
                self.logger.error(f"Unexpected error loading page {page_num}, attempt {attempt + 1}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
        
        self.logger.error(f"Failed to load page {page_num} after {self.retry_attempts} attempts")
        return []
    
    async def _scrape_page_with_selenium(self, url: str, page_num: int) -> List[Dict[str, any]]:
        """Scrape page using Selenium (runs in thread pool)"""
        from .parsers.selenium_parser import SeleniumParser
        
        if not isinstance(self.parser, SeleniumParser):
            return []
        
        for attempt in range(self.retry_attempts):
            try:
                quotes = await asyncio.to_thread(self.parser.parse_quotes_from_url, url)
                return quotes
            except Exception as e:
                self.logger.error(f"Selenium error loading page {page_num}, attempt {attempt + 1}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
        
        return []
    
    async def _has_next_page(self, current_page: int) -> bool:
        """Check for the presence of the next page"""
        url = f"{self.base_url}/page/{current_page}/" if current_page > 1 else self.base_url + "/"
        
        if self.parser_type == 'selenium':
            from .parsers.selenium_parser import SeleniumParser
            if isinstance(self.parser, SeleniumParser):
                try:
                    return await asyncio.to_thread(self.parser.has_next_page_from_url, url)
                except Exception as e:
                    self.logger.debug(f"Error checking next page with Selenium: {str(e)}")
                    return False
        
        try:
            async with self.session.get(url, timeout=self.timeout) as response:
                if response.status == 200:
                    html = await response.text()
                    return self.parser.has_next_page(html)
        except Exception as e:
            self.logger.debug(f"Error checking next page: {str(e)}")
            return False
        
        return False

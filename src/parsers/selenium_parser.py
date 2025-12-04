import re

from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from .base_parser import BaseParser


class SeleniumParser(BaseParser):
    """Parser using Selenium WebDriver"""
    
    def __init__(self, driver: Optional[webdriver.Chrome] = None):
        """
        Initialize Selenium parser
        
        Args:
            driver: Optional WebDriver instance. If not provided, will create a new one.
        """
        self.driver = driver
        self._own_driver = driver is None
    
    def _get_driver(self) -> webdriver.Chrome:
        """Get or create WebDriver instance"""
        if self.driver is None:
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        return self.driver
    
    def parse_quotes_from_url(self, url: str) -> List[Dict[str, any]]:
        """
        Parse quotes directly from URL using Selenium (more efficient)
        
        Args:
            url: URL to parse
            
        Returns:
            List of quote dictionaries
        """
        driver = self._get_driver()
        quotes = []
        
        try:
            driver.get(url)
            
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "quote"))
                )
            except TimeoutException:
                return []
            
            quote_elements = driver.find_elements(By.CLASS_NAME, "quote")
            
            for quote_element in quote_elements:
                try:
                    quote_data = self._parse_single_quote(quote_element)
                    if quote_data:
                        quotes.append(quote_data)
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return quotes
    
    def parse_quotes_from_html(self, html: str) -> List[Dict[str, any]]:
        """Parsing quotes from HTML string through Selenium"""
        driver = self._get_driver()
        quotes = []
        
        try:
            driver.get("data:text/html;charset=utf-8," + html)
            
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "quote"))
                )
            except TimeoutException:
                return []
            
            quote_elements = driver.find_elements(By.CLASS_NAME, "quote")
            
            for quote_element in quote_elements:
                try:
                    quote_data = self._parse_single_quote(quote_element)
                    if quote_data:
                        quotes.append(quote_data)
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return quotes
    
    def _parse_single_quote(self, quote_element) -> Optional[Dict[str, any]]:
        """Parsing one quote element"""
        try:
            text_element = quote_element.find_element(By.CLASS_NAME, "text")
            author_element = quote_element.find_element(By.CLASS_NAME, "author")
            tags_elements = quote_element.find_elements(By.CLASS_NAME, "tag")
            
            quote_data = {
                'text': text_element.text.strip('"'),
                'author': author_element.text.strip(),
                'tags': [tag.text.strip() for tag in tags_elements]
            }
            
            return quote_data
            
        except NoSuchElementException:
            return None
        except Exception:
            return None
    
    def has_next_page_from_url(self, url: str) -> bool:
        """Check for the presence of the next page from URL"""
        driver = self._get_driver()
        
        try:
            driver.get(url)
            next_button = driver.find_element(By.CSS_SELECTOR, "li.next")
            return next_button is not None
        except NoSuchElementException:
            return False
        except Exception:
            return False
    
    def has_next_page(self, html: str) -> bool:
        """Check for the presence of the next page"""
        driver = self._get_driver()
        
        try:
            driver.get("data:text/html;charset=utf-8," + html)
            next_button = driver.find_element(By.CSS_SELECTOR, "li.next")
            return next_button is not None
        except NoSuchElementException:
            return False
        except Exception:
            return False
    
    def extract_page_number(self, html: str) -> int:
        """Extract the number of the current page"""
        driver = self._get_driver()
        
        try:
            driver.get("data:text/html;charset=utf-8," + html)
            pagination = driver.find_element(By.CLASS_NAME, "pager")
            current_page = pagination.find_element(By.CLASS_NAME, "current")
            
            match = re.search(r'(\d+)', current_page.text)
            if match:
                return int(match.group(1))
        except (NoSuchElementException, Exception):
            pass
        
        return 1
    
    def has_no_quotes(self, html: str) -> bool:
        """Check if page contains 'No quotes found!' message"""
        return "No quotes found!" in html
    
    def close(self):
        """Close WebDriver if we own it"""
        if self._own_driver and self.driver:
            self.driver.quit()
            self.driver = None

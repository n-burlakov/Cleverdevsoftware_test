import re
import aiohttp
import asyncio

from typing import Dict, Optional
from bs4 import BeautifulSoup

from .exceptions import AuthenticationError
from .logger import ScraperLogger


class Authenticator:
    """Class for authentication on the site"""
    
    def __init__(self, config: dict, logger: ScraperLogger):
        self.config = config
        self.logger = logger.get_logger()
        self.session: Optional[aiohttp.ClientSession] = None
        self.retry_attempts = config.get('auth', {}).get('retry_attempts', 3)
        self.retry_delay = config.get('auth', {}).get('retry_delay', 2)
        self.timeout = aiohttp.ClientTimeout(total=config.get('scraping', {}).get('timeout', 10))
    
    async def __aenter__(self):
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        self.session = aiohttp.ClientSession(cookie_jar=cookie_jar, timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self) -> bool:
        """Perform authentication with retry mechanism"""
        auth_config = self.config['auth']
        login_url = auth_config['login_url']
        
        for attempt in range(self.retry_attempts):
            try:
                self.logger.info(f"Authentication attempt {attempt + 1}/{self.retry_attempts}")
                
                async with self.session.get(login_url) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to load login page: status {response.status}")
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        return False
                    
                    html = await response.text()
                    csrf_token = self._extract_csrf_token(html)
                    
                    if not csrf_token:
                        self.logger.error("CSRF token not found in login page")
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        return False
                    
                    self.logger.debug(f"CSRF token extracted: {csrf_token[:20]}...")
                
                login_data = {
                    'csrf_token': csrf_token,
                    'username': auth_config['username'],
                    'password': auth_config['password']
                }
                
                async with self.session.post(login_url, data=login_data, allow_redirects=True) as login_response:
                    if login_response.status not in [200, 302]:
                        self.logger.error(f"Authentication error: status {login_response.status}")
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        return False
                    
                    login_html = await login_response.text()
                    
                    if self._check_authentication_success(login_html, auth_config['username']):
                        self.logger.info(f"Successful authentication for user {auth_config['username']}")
                        return True
                    else:
                        self.logger.warning(f"Authentication check failed on attempt {attempt + 1}")
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        return False
                        
            except asyncio.TimeoutError:
                self.logger.error(f"Timeout during authentication attempt {attempt + 1}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                return False
                
            except Exception as e:
                self.logger.error(f"Authentication error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                return False
        
        self.logger.error("Authentication failed after all retry attempts")
        return False
    
    def _extract_csrf_token(self, html: str) -> Optional[str]:
        """Extract CSRF token from HTML using BeautifulSoup for reliability"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            csrf_input = soup.find('input', {'name': 'csrf_token'})
            if csrf_input and csrf_input.get('value'):
                return csrf_input['value']
            
            match = re.search(r'name=["\']csrf_token["\']\s+value=["\'](.+?)["\']', html)
            if match:
                return match.group(1)
            
            match = re.search(r'csrf_token["\']\s*:\s*["\'](.+?)["\']', html)
            if match:
                return match.group(1)
                
        except Exception as e:
            self.logger.debug(f"Error extracting CSRF token: {str(e)}")
        
        return None
    
    def _check_authentication_success(self, html: str, username: str) -> bool:
        """Check if authentication was successful"""
        indicators = [
            username.lower() in html.lower(),
            'logout' in html.lower(),
            'log out' in html.lower(),
            'successfully logged in' in html.lower(),
        ]
        
        if '/login' not in html or len(html) > 5000:
            if 'quote' in html.lower() or 'quotes' in html.lower():
                return True
        
        return any(indicators)

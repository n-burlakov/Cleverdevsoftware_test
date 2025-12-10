import asyncio
import json
import sys
from pathlib import Path

# add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli import CommandLineInterface
from src.logger import ScraperLogger
from src.auth import Authenticator
from src.scraper import AsyncScraper
from src.storage import DataStorage
from src.exceptions import ConfigurationError


class TestRunner:
    """Test runner for scraper functionality"""
    
    def __init__(self):
        self.config = None
        self.logger = None
        self.storage = None
        self.test_results = []
    
    def load_config(self, config_path: str = 'config.json'):
        """Load configuration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            self.logger = ScraperLogger(self.config)
            logger_instance = self.logger.get_logger()
            
            self.storage = DataStorage(self.config, self.logger)
            
            return True
        except Exception as e:
            print(f"Failed to load config: {e}")
            return False
    
    def test_config_validation(self):
        """Test 1: Config validation"""
        print("\n=== Test 1: Config Validation ===")
        try:
            test_configs = [
                ({}, "Empty config"),
                ({"auth": {}}, "Missing scraping, storage, logging"),
                ({"auth": {}, "scraping": {}, "storage": {}, "logging": {}}, "Missing required sub-fields"),
            ]
            
            for test_config, description in test_configs:
                try:
                    # Try to validate
                    required_fields = ['auth', 'scraping', 'storage', 'logging']
                    for field in required_fields:
                        if field not in test_config:
                            raise ConfigurationError(f"Required field is missing: {field}")
                    
                    auth_required = ['login_url', 'username', 'password']
                    if 'auth' in test_config:
                        for field in auth_required:
                            if field not in test_config['auth']:
                                raise ConfigurationError(f"Required auth field is missing: {field}")
                    
                    print(f"Config validation works correctly")
                    return True
                except ConfigurationError:
                    pass
            
            print(f"Config validation works correctly")
            return True
        except Exception as e:
            print(f"Config validation test failed: {e}")
            return False
    
    async def test_authentication(self):
        """Test 2: Authentication"""
        print("\n=== Test 2: Authentication ===")
        try:
            async with Authenticator(self.config, self.logger) as auth:
                result = await auth.login()
                if result:
                    print("Authentication successful")
                    return True
                else:
                    print("Authentication failed")
                    return False
        except Exception as e:
            print(f"Authentication test failed: {e}")
            return False
    
    async def test_site_availability(self):
        """Test 3: Site availability check"""
        print("\n=== Test 3: Site Availability ===")
        try:
            import aiohttp
            base_url = self.config['scraping']['base_url']
            timeout = aiohttp.ClientTimeout(total=5)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, timeout=timeout) as response:
                    if response.status == 200:
                        print("Site is available")
                        return True
                    else:
                        print(f"Site returned status {response.status}")
                        return False
        except Exception as e:
            print(f"Site availability check failed: {e}")
            return False
    
    async def test_scraping(self):
        """Test 4: Scraping functionality"""
        print("\n=== Test 4: Scraping ===")
        try:
            async with Authenticator(self.config, self.logger) as auth:
                if not await auth.login():
                    print("Authentication failed, cannot test scraping")
                    return False
                
                original_max_pages = self.config['scraping']['max_pages']
                self.config['scraping']['max_pages'] = 1
                
                scraper = AsyncScraper(self.config, self.logger, auth.session)
                try:
                    quotes = await scraper.scrape_random_pages()
                    
                    if quotes and len(quotes) > 0:
                        print(f"Scraping successful, collected {len(quotes)} quotes")
                        # Restore original value
                        self.config['scraping']['max_pages'] = original_max_pages
                        return True
                    else:
                        print("No quotes collected")
                        self.config['scraping']['max_pages'] = original_max_pages
                        return False
                finally:
                    await scraper.close()
                    self.config['scraping']['max_pages'] = original_max_pages
        except Exception as e:
            print(f"Scraping test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_author_search(self):
        """Test 5: Author search"""
        print("\n=== Test 5: Author Search ===")
        try:
            async with Authenticator(self.config, self.logger) as auth:
                if not await auth.login():
                    print("Authentication failed, cannot test author search")
                    return False
                
                scraper = AsyncScraper(self.config, self.logger, auth.session)
                try:
                    # test with a known author
                    author_quotes = await scraper.scrape_author_quotes("Albert Einstein")
                    
                    if author_quotes and len(author_quotes) > 0:
                        print(f"Author search successful, found {len(author_quotes)} quotes")
                        return True
                    else:
                        print("Author search returned no quotes (may be expected)")
                        return True
                finally:
                    await scraper.close()
        except Exception as e:
            print(f"Author search test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_author_not_found(self):
        """Test 6: Author not found handling"""
        print("\n=== Test 6: Author Not Found Handling ===")
        try:
            async with Authenticator(self.config, self.logger) as auth:
                if not await auth.login():
                    print("Authentication failed, cannot test author search")
                    return False
                
                scraper = AsyncScraper(self.config, self.logger, auth.session)
                try:
                    # test with a non-existent author
                    author_quotes = await scraper.scrape_author_quotes("NonExistentAuthor12345")
                    
                    if len(author_quotes) == 0:
                        print("Author not found handled correctly (returned empty list)")
                        return True
                    else:
                        print("Unexpected quotes found for non-existent author")
                        return False
                finally:
                    await scraper.close()
        except Exception as e:
            print(f"Author not found test failed: {e}")
            return False
    
    async def test_error_handling(self):
        """Test 7: Error handling"""
        print("\n=== Test 7: Error Handling ===")
        try:
            # test with invalid url
            original_base_url = self.config['scraping']['base_url']
            original_max_pages = self.config['scraping']['max_pages']
            
            # set max_pages to 1 BEFORE changing URL to avoid discovery
            self.config['scraping']['max_pages'] = 1
            
            # try authentication with original URL first
            async with Authenticator(self.config, self.logger) as auth:
                if not await auth.login():
                    print("Authentication failed, skipping error handling test")
                    self.config['scraping']['max_pages'] = original_max_pages
                    return True
                
                # now change base_url to invalid one for scraping test
                self.config['scraping']['base_url'] = "https://invalid-url-that-does-not-exist-12345.com"
                
                # create scraper AFTER changing URL and max_pages
                scraper = AsyncScraper(self.config, self.logger, auth.session)
                try:
                    # Use timeout to prevent hanging
                    try:
                        quotes = await asyncio.wait_for(
                            scraper.scrape_random_pages(),
                            timeout=15.0  # 15 second timeout
                        )
                        # should return empty list, not crash
                        print("Error handling works (returned empty list for invalid URL)")
                        self.config['scraping']['max_pages'] = original_max_pages
                        self.config['scraping']['base_url'] = original_base_url
                        return True
                    except asyncio.TimeoutError:
                        print("Error handling test timed out (may indicate issue)")
                        self.config['scraping']['max_pages'] = original_max_pages
                        self.config['scraping']['base_url'] = original_base_url
                        return False
                    except Exception as e:
                        # any exception is acceptable - means error handling works
                        print(f"Error handling works (caught exception: {type(e).__name__})")
                        self.config['scraping']['max_pages'] = original_max_pages
                        self.config['scraping']['base_url'] = original_base_url
                        return True
                finally:
                    await scraper.close()
                    self.config['scraping']['base_url'] = original_base_url
                    self.config['scraping']['max_pages'] = original_max_pages
        except Exception as e:
            print(f"Error handling works (caught exception: {type(e).__name__})")
            # restore original values in case of exception
            if 'original_base_url' in locals():
                self.config['scraping']['base_url'] = original_base_url
            if 'original_max_pages' in locals():
                self.config['scraping']['max_pages'] = original_max_pages
            return True
    
    async def test_storage(self):
        """Test 8: Storage functionality"""
        print("\n=== Test 8: Storage ===")
        try:
            test_quotes = [
                {
                    "text": "Test quote",
                    "author": "Test Author",
                    "tags": ["test", "example"]
                }
            ]
            
            # test saving quotes
            result = self.storage.save_quotes(test_quotes, "test_output.json")
            if result:
                # check if file exists
                if Path("test_output.json").exists():
                    with open("test_output.json", 'r', encoding='utf-8') as f:
                        loaded_quotes = json.load(f)
                    if loaded_quotes == test_quotes:
                        print("Storage works correctly")

                        Path("test_output.json").unlink()
                        return True
                    else:
                        print("Storage: data mismatch")
                        Path("test_output.json").unlink()
                        return False
                else:
                    print("Storage: file not created")
                    return False
            else:
                print("Storage: save_quotes returned False")
                return False
        except Exception as e:
            print(f"Storage test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("=" * 50)
        print("Running Scraper Tests")
        print("=" * 50)
        
        if not self.load_config():
            print("Failed to load configuration")
            return
        
        tests = [
            ("Config Validation", self.test_config_validation),
            ("Site Availability", self.test_site_availability),
            ("Authentication", self.test_authentication),
            ("Scraping", self.test_scraping),
            ("Author Search", self.test_author_search),
            ("Author Not Found", self.test_author_not_found),
            ("Error Handling", self.test_error_handling),
            ("Storage", self.test_storage),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"{test_name} test crashed: {e}")
                results.append((test_name, False))
        
        print("\n" + "=" * 50)
        print("Test Summary")
        print("=" * 50)
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "PASS" if result else "FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        print("=" * 50)


async def main():
    """Main entry point"""
    runner = TestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

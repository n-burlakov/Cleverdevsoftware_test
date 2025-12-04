# Quotes Scraper

An asynchronous Python scraper for quotes.toscrape.com with authorization, data collection, and author search functionality.

## Features

- **Site Authentication**: Automatic login with credentials from config.json
- **Data Collection**: Scraping quotes from random pages with pagination support
- **Author Search**: Search for quotes by specific author name
- **Multiple Parser Backends**: Support for BeautifulSoup (BS4) and Selenium WebDriver
- **Automatic Page Discovery**: Automatically discovers all pages when max_pages is not set
- **Retry Mechanism**: Automatic retry (up to 3 attempts) for network errors
- **Error Handling**: Robust error handling with graceful degradation
- **Logging**: Comprehensive logging of all operations to `logs/script.log`
- **Flexible Configuration**: All parameters configurable via `config.json`
- **CLI Arguments**: Override configuration via command-line arguments

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Cleverdevsoftware_test
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.json` to configure the scraper:

### Parser Types

The scraper supports two parsing backends:

- **`bs4`** (default): Uses BeautifulSoup for fast HTML parsing. Recommended for most use cases.
- **`selenium`**: Uses Selenium WebDriver for JavaScript-heavy pages. Requires Chrome/Chromium browser.

Set `parser_type` in the `scraping` section of `config.json`:

```json
{
    "auth": {
      "login_url": "https://quotes.toscrape.com/login",
      "username": "test_user",
      "password": "test_pass",
      "retry_attempts": 3,
      "retry_delay": 2
    },
    "scraping": {
      "base_url": "https://quotes.toscrape.com",
      "max_pages": 5,  # Set to null or 0 for automatic page discovery
      "retry_attempts": 3,
      "retry_delay": 2,
      "timeout": 10,
      "random_pages": true,
      "parser_type": "bs4"  # Options: "bs4" or "selenium"
    },
    "storage": {
      "output_file": "outputs/output.json",
      "author_quotes_file": "outputs/author_quotes.json",
      "log_file": "logs/script.log"
    },
    "logging": {
      "level": "INFO",
      "format": "[%(asctime)s] %(levelname)s: %(message)s",
      "date_format": "%Y-%m-%d %H:%M:%S"
    }
}
```

## Usage

### Basic Usage

Run the scraper to collect quotes from random pages:
```bash
python main.py
```

### Search for Author Quotes

Search for quotes by a specific author:
```bash
python main.py --author "Albert Einstein"
```

### Override Configuration

Override number of pages to scrape:
```bash
python main.py --pages 10
```

Override output file:
```bash
python main.py --output custom_output.json
```

### Combined Usage

```bash
python main.py --author "Mark Twain" --pages 20 --output author_quotes.json
```

### Parser Selection

The parser type is configured in `config.json`. To use Selenium instead of BeautifulSoup:

```json
{
  "scraping": {
    "parser_type": "selenium"
  }
}
```

**Note**: When using Selenium:
- Chrome/Chromium browser must be installed
- ChromeDriver will be automatically downloaded via webdriver-manager
- Selenium runs in headless mode by default
- Slightly slower than BS4 but better for JavaScript-rendered content

### Automatic Page Discovery

If `max_pages` is set to `null` or `0` in `config.json`, the scraper will automatically discover all available pages by checking pagination until it encounters a page with "No quotes found!" message. This is useful when you don't know the total number of pages in advance.

```json
{
  "scraping": {
    "max_pages": null  # or 0 for automatic discovery
  }
}
```

## Command-Line Arguments

- `--pages N`: Number of pages to parse (overrides config.json)
- `--output FILE`: Path to output file (overrides config.json, must be .json)
- `--author NAME`: Name of the author to search for quotes
- `--config PATH`: Path to configuration file (default: config.json)


## Output Format

### output.json
```json
[
  {
    "text": "The world as we have created it...",
    "author": "Albert Einstein",
    "tags": ["change", "deep-thoughts", "thinking"]
  },
  ...
]
```

### author_quotes.json
```json
{
  "author": "Albert Einstein",
  "total_quotes": 3,
  "quotes": [
    {
      "text": "The world as we have created it...",
      "author": "Albert Einstein",
      "tags": ["change", "deep-thoughts"]
    },
    ...
  ]
}
```

## Error Handling

The scraper includes comprehensive error handling:

- **Network Errors**: Automatic retry up to 3 times with configurable delay
- **Site Unavailability**: Checks site availability before starting
- **Authentication Failures**: Detailed error logging and graceful failure
- **Missing Elements**: Continues processing even if some elements are missing
- **Invalid Configuration**: Validates configuration file on startup

## Logging

All operations are logged to `logs/script.log` with timestamps:
```
[2025-12-03 13:28:57] INFO: Starting scraper for quotes.toscrape.com
[2025-12-03 13:28:57] INFO: Performing authentication...
[2025-12-03 13:28:58] INFO: Successful authentication for user test_user
[2025-12-03 13:28:58] INFO: Starting data collection...
```

## Requirements

- Python 3.8+
- aiohttp >= 3.8.0
- beautifulsoup4 >= 4.12.0
- lxml >= 4.9.0
- requests >= 2.31.0
- selenium >= 4.15.0 (required for Selenium parser)
- webdriver-manager >= 4.0.0 (required for Selenium parser)

### Selenium Requirements

If using the Selenium parser:
- Chrome or Chromium browser must be installed
- ChromeDriver will be automatically managed by webdriver-manager
- No manual driver installation needed

## Troubleshooting

### Authentication Failed
- Check that `username` and `password` in `config.json` are correct
- Verify that the login URL is accessible
- Check logs for detailed error messages

### No Quotes Collected
- Verify internet connection
- Check if the site is accessible
- Review logs for specific error messages
- Try increasing `timeout` in config.json

### Author Not Found
- Verify author name spelling (case-insensitive)
- Check logs to see which pages were searched
- Try searching without authentication (if site allows)

### Selenium Parser Issues
- Ensure Chrome/Chromium is installed on your system
- Check that ChromeDriver can be downloaded (internet connection required)
- For headless mode issues, try running without `--headless` flag (modify selenium_parser.py)
- Check logs for Selenium-specific error messages
- On Linux, you may need to install additional dependencies:
  ```bash
  sudo apt-get install chromium-browser chromium-chromedriver
  ```

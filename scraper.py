
# scraper.py
import requests
from bs4 import BeautifulSoup
import json
import logging
import re
from urllib.parse import urlparse
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file: {e}")
        return {}

def validate_url(url):
    """Validate if the URL is properly formatted."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def scrape_site(url, save_file="scraped_data.json", config_data=None):
    """
    Scrapes the given URL and saves parsed data with comprehensive error handling.
    
    Args:
        url (str): The URL to scrape
        save_file (str): Path to save the scraped data
        config_data (dict): Configuration data from YAML file
        
    Returns:
        dict: Scraped data or None if failed
    """
    if not validate_url(url):
        logger.error(f"Invalid URL format: {url}")
        return None
    
    # Set default headers to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Use configuration if available
    if config_data and 'scraper' in config_data:
        scraper_config = config_data['scraper']
        timeout = scraper_config.get('timeout', 30)
        headers.update(scraper_config.get('headers', {}))
    else:
        timeout = 30
    
    try:
        logger.info(f"Starting to scrape: {url}")
        
        # Make request with timeout and headers
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        logger.info(f"Successfully fetched page. Status: {response.status_code}")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract data based on configuration or defaults
        scraped_data = {}
        
        if config_data and 'scraper' in config_data:
            extract_config = config_data['scraper'].get('extract', {})
            
            # Extract headings
            if extract_config.get('headings', True):
                heading_tags = extract_config.get('heading_tags', ['h1', 'h2', 'h3'])
                headings = [h.get_text().strip() for h in soup.find_all(heading_tags)]
                scraped_data['headings'] = headings
                logger.info(f"Found {len(headings)} headings")
            
            # Extract links
            if extract_config.get('links', False):
                links = [a.get('href') for a in soup.find_all('a', href=True)]
                scraped_data['links'] = links[:50]  # Limit to first 50 links
                logger.info(f"Found {len(scraped_data['links'])} links")
            
            # Extract meta description
            if extract_config.get('meta_description', False):
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                scraped_data['meta_description'] = meta_desc.get('content', '') if meta_desc else ''
            
            # Extract page title
            if extract_config.get('title', True):
                title = soup.find('title')
                scraped_data['title'] = title.get_text().strip() if title else ''
                
        else:
            # Default extraction (headings only)
            headings = [h.get_text().strip() for h in soup.find_all(['h1','h2','h3'])]
            scraped_data['headings'] = headings
            title = soup.find('title')
            scraped_data['title'] = title.get_text().strip() if title else ''
            logger.info(f"Found {len(headings)} headings (default extraction)")
        
        # Add metadata
        scraped_data['url'] = url
        scraped_data['scraped_at'] = response.headers.get('Date', 'Unknown')
        scraped_data['content_length'] = len(response.text)
        
        # Save results
        try:
            with open(save_file, 'w', encoding='utf-8') as f:
                json.dump(scraped_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Data saved to {save_file}")
        except IOError as e:
            logger.error(f"Failed to save data to {save_file}: {e}")
            return None
        
        return scraped_data
        
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout for URL: {url}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error for URL: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error for URL {url}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for URL {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while scraping {url}: {e}")
        return None

def scrape_multiple_sites(urls, save_dir="scraped_data"):
    """
    Scrape multiple URLs and save each result separately.
    
    Args:
        urls (list): List of URLs to scrape
        save_dir (str): Directory to save scraped data
    """
    import os
    
    # Create directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    config_data = load_config()
    results = {}
    
    for i, url in enumerate(urls):
        if validate_url(url):
            save_file = os.path.join(save_dir, f"site_{i+1}.json")
            logger.info(f"Scraping site {i+1}/{len(urls)}: {url}")
            data = scrape_site(url, save_file, config_data)
            if data:
                results[url] = data
        else:
            logger.warning(f"Skipping invalid URL: {url}")
    
    # Save summary
    summary_file = os.path.join(save_dir, "scraping_summary.json")
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_urls': len(urls),
                'successful_scrapes': len(results),
                'failed_scrapes': len(urls) - len(results),
                'results': results
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"Scraping summary saved to {summary_file}")
    except IOError as e:
        logger.error(f"Failed to save summary: {e}")

# Example usage:
if __name__ == "__main__":
    # Load configuration
    config = load_config()
    
    # Use config URL if available, otherwise use example
    target_url = "https://news.ycombinator.com"
    if config and 'scraper' in config and 'target_url' in config['scraper']:
        target_url = config['scraper']['target_url']
        if not target_url.startswith('http'):
            target_url = 'https://' + target_url
    
    # Scrape single site
    scrape_site(target_url, save_file="hn_headings.json", config_data=config)

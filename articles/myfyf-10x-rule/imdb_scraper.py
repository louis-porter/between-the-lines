import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IMDBBoxOfficeScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://pro.imdb.com"
        self.data = []
        
    def get_page(self, url, max_retries=3):
        """Get page content with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
    
    def clean_currency(self, text):
        """Clean currency text and convert to number"""
        if not text:
            return None
        # Remove currency symbols, commas, and whitespace
        cleaned = re.sub(r'[,$\s]', '', text.strip())
        try:
            return int(cleaned)
        except ValueError:
            return None
    
    def extract_movie_links(self, year_url):
        """Extract movie links from yearly box office page"""
        logger.info(f"Scraping year page: {year_url}")
        response = self.get_page(year_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        movie_links = []
        
        # Find all movie links in the table
        links = soup.find_all('a', class_='a-link-normal')
        for link in links:
            href = link.get('href')
            if href and '/releasegroup/' in href:
                full_url = urljoin(self.base_url, href)
                movie_title = link.text.strip()
                movie_links.append((movie_title, full_url))
                logger.info(f"Found movie: {movie_title}")
        
        return movie_links
    
    def extract_box_office_data(self, movie_url, movie_title):
        """Extract box office data from movie page"""
        logger.info(f"Extracting data for: {movie_title}")
        response = self.get_page(movie_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the box office summary section
        box_office_section = soup.find('div', id='box_office_summary')
        if not box_office_section:
            logger.warning(f"No box office section found for {movie_title}")
            return None
        
        data = {
            'title': movie_title,
            'url': movie_url,
            'opening_weekend': None,
            'gross_world': None,
            'budget': None,
            'gross_usa_canada': None
        }
        
        # Extract different box office metrics
        sections = {
            'opening_wknd_summary': 'opening_weekend',
            'gross_world_summary': 'gross_world',
            'budget_summary': 'budget',
            'gross_usa_summary': 'gross_usa_canada'
        }
        
        for section_class, data_key in sections.items():
            section = box_office_section.find('div', class_=section_class)
            if section:
                value_div = section.find('div', class_='a-column a-span5 a-text-right a-span-last')
                if value_div:
                    value_text = value_div.text.strip()
                    data[data_key] = self.clean_currency(value_text)
                    logger.info(f"{data_key}: {value_text}")
        
        return data
    
    def scrape_year(self, year):
        """Scrape all movies from a specific year"""
        year_url = f"{self.base_url}/boxoffice/year/world/{year}/"
        movie_links = self.extract_movie_links(year_url)
        
        year_data = []
        for movie_title, movie_url in movie_links:
            try:
                movie_data = self.extract_box_office_data(movie_url, movie_title)
                if movie_data:
                    movie_data['year'] = year
                    year_data.append(movie_data)
                    self.data.append(movie_data)
                
                # Be respectful with delays
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing {movie_title}: {e}")
                continue
        
        logger.info(f"Completed year {year}: {len(year_data)} movies scraped")
        return year_data
    
    def scrape_all_years(self, start_year=1977, end_year=2024):
        """Scrape all years from start_year to end_year"""
        logger.info(f"Starting scrape from {start_year} to {end_year}")
        
        for year in range(start_year, end_year + 1):
            try:
                self.scrape_year(year)
                # Longer delay between years
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error scraping year {year}: {e}")
                continue
        
        logger.info(f"Scraping completed. Total movies: {len(self.data)}")
    
    def save_to_csv(self, filename='imdb_box_office_data.csv'):
        """Save scraped data to CSV file"""
        if not self.data:
            logger.warning("No data to save")
            return
        
        df = pd.DataFrame(self.data)
        # Reorder columns
        columns = ['year', 'title', 'opening_weekend', 'gross_world', 'gross_usa_canada', 'budget', 'url']
        df = df.reindex(columns=columns)
        
        df.to_csv(filename, index=False)
        logger.info(f"Data saved to {filename}")
        
        # Print summary statistics
        print(f"\nScraping Summary:")
        print(f"Total movies scraped: {len(df)}")
        print(f"Years covered: {df['year'].min()} - {df['year'].max()}")
        print(f"Movies with opening weekend data: {df['opening_weekend'].notna().sum()}")
        print(f"Movies with worldwide gross data: {df['gross_world'].notna().sum()}")
        
        return df

# Usage example
def main():
    scraper = IMDBBoxOfficeScraper()
    
    # Test with a single year first
    print("Testing with year 2000...")
    test_data = scraper.scrape_year(2000)
    
    # Uncomment below to scrape all years (this will take a long time!)
    # scraper.scrape_all_years(1977, 2024)
    
    # Save the data
    df = scraper.save_to_csv('imdb_test_data.csv')
    
    # Display first few rows
    if not df.empty:
        print("\nFirst few rows of scraped data:")
        print(df.head())

if __name__ == "__main__":
    main()
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

def scrape_team_salary_data(url):
    """
    Scrape team names and adjusted gross salary values from the table
    """
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to the page
        driver.get(url)
        
        # Wait for table to load and be stable
        wait = WebDriverWait(driver, 15)
        table = wait.until(EC.presence_of_element_located((By.ID, "table")))
        
        # Wait a bit more for any dynamic content to load
        time.sleep(2)
        
        # Get all row data in one go to avoid stale element issues
        rows_data = driver.execute_script("""
            var table = document.getElementById('table');
            var rows = table.querySelectorAll('tbody tr');
            var data = [];
            
            for (var i = 0; i < rows.length; i++) {
                var row = rows[i];
                var cells = row.querySelectorAll('td');
                
                if (cells.length >= 5) {
                    var teamLink = cells[0].querySelector('a.firstcol');
                    var teamName = teamLink ? teamLink.textContent.trim() : 'N/A';
                    var adjGross = cells[4].textContent.trim();
                    
                    data.push({
                        'team_name': teamName,
                        'adj_gross_gbp': adjGross
                    });
                }
            }
            
            return data;
        """)
        
        return rows_data
        
    except Exception as e:
        print(f"Error scraping data: {e}")
        return []
        
    finally:
        driver.quit()

def scrape_all_columns(url):
    """
    Scrape all relevant columns from the table
    """
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(url)
        
        wait = WebDriverWait(driver, 15)
        table = wait.until(EC.presence_of_element_located((By.ID, "table")))
        
        # Wait for content to stabilize
        time.sleep(2)
        
        # Use JavaScript to extract all data at once
        complete_data = driver.execute_script("""
            var table = document.getElementById('table');
            var rows = table.querySelectorAll('tbody tr');
            var data = [];
            
            for (var i = 0; i < rows.length; i++) {
                var row = rows[i];
                var cells = row.querySelectorAll('td');
                
                if (cells.length >= 9) {
                    var teamLink = cells[0].querySelector('a.firstcol');
                    var teamName = teamLink ? teamLink.textContent.trim() : 'N/A';
                    
                    var rowData = {
                        'team_name': teamName,
                        'club_code': cells[1].textContent.trim(),
                        'weekly_gross_gbp': cells[2].textContent.trim(),
                        'annual_gross_gbp': cells[3].textContent.trim(),
                        'adj_gross_gbp': cells[4].textContent.trim(),
                        'keeper_gbp': cells[5].textContent.trim(),
                        'defense_gbp': cells[6].textContent.trim(),
                        'midfield_gbp': cells[7].textContent.trim(),
                        'forward_gbp': cells[8].textContent.trim()
                    };
                    
                    data.push(rowData);
                }
            }
            
            return data;
        """)
        
        return complete_data
        
    except Exception as e:
        print(f"Error scraping data: {e}")
        return []
        
    finally:
        driver.quit()

def scrape_multiple_seasons(base_url, seasons):
    """
    Scrape data from multiple seasons
    
    Args:
        base_url (str): Base URL pattern with {} placeholder for season
        seasons (list): List of season strings (e.g., ['2013-2014', '2014-2015'])
    
    Returns:
        list: Combined data from all seasons with season column added
    """
    all_data = []
    
    for season in seasons:
        print(f"\nScraping season: {season}")
        
        # Format URL for this season
        season_url = base_url.format(season)
        print(f"URL: {season_url}")
        
        try:
            # Scrape data for this season
            season_data = scrape_all_columns(season_url)
            
            # Clean money values to integers
            season_data = clean_data_money_columns(season_data)
            
            # Add season column to each record
            for record in season_data:
                record['season'] = season
            
            all_data.extend(season_data)
            
            print(f"Successfully scraped {len(season_data)} teams for {season}")
            
            # Add delay between requests to be respectful
            time.sleep(2)
            
        except Exception as e:
            print(f"Error scraping season {season}: {e}")
            continue
    
    return all_data

def generate_season_list(start_year, end_year):
    """
    Generate a list of season strings
    
    Args:
        start_year (int): Starting year (e.g., 2013)
        end_year (int): Ending year (e.g., 2023)
    
    Returns:
        list: List of season strings like ['2013-2014', '2014-2015', ...]
    """
    seasons = []
    for year in range(start_year, end_year):
        season = f"{year}-{year + 1}"
        seasons.append(season)
    
    return seasons

def clean_money_value(money_str):
    """
    Convert money string to integer
    
    Args:
        money_str (str): Money string like '£ 47,070,570' or '£47,070,570'
    
    Returns:
        int: Clean integer value like 47070570
    """
    if not money_str or money_str == 'N/A':
        return 0
    
    # Remove £ symbol, spaces, and commas
    cleaned = money_str.replace('£', '').replace(' ', '').replace(',', '')
    
    try:
        return int(cleaned)
    except ValueError:
        return 0

def clean_data_money_columns(data):
    """
    Clean all money columns in the dataset
    
    Args:
        data (list): List of dictionaries with money values
    
    Returns:
        list: Data with cleaned integer money values
    """
    money_columns = [
        'weekly_gross_gbp',
        'annual_gross_gbp', 
        'adj_gross_gbp',
        'keeper_gbp',
        'defense_gbp',
        'midfield_gbp',
        'forward_gbp'
    ]
    
    for record in data:
        for col in money_columns:
            if col in record:
                record[col] = clean_money_value(record[col])
    
    return data

def scrape_single_season(url):
    """
    Wrapper function to scrape a single season with better error handling
    """
    try:
        data = scrape_all_columns(url)
        return data
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

# Alternative approach using BeautifulSoup (if you have the HTML already)
def scrape_with_beautifulsoup(html_content):
    """
    Parse the HTML content directly using BeautifulSoup
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', id='table')
    
    if not table:
        print("Table not found")
        return []
    
    rows = table.find('tbody').find_all('tr')
    data = []
    
    for row in rows:
        cells = row.find_all('td')
        
        if len(cells) >= 5:
            # Extract team name
            team_link = cells[0].find('a', class_='firstcol')
            team_name = team_link.text.strip() if team_link else 'N/A'
            
            # Extract adjusted gross value (5th column)
            adj_gross_value = cells[4].text.strip()
            
            data.append({
                'team_name': team_name,
                'adj_gross_gbp': adj_gross_value
            })
    
    return data

# Usage example
if __name__ == "__main__":
    # Base URL pattern - {} will be replaced with season
    base_url = "https://www.capology.com/uk/premier-league/payrolls/{}/"
    
    # Method 1: Define seasons manually
    seasons_manual = [
        "2013-2014",
        "2014-2015", 
        "2015-2016",
        "2016-2017",
        "2017-2018",
        "2018-2019",
        "2019-2020",
        "2020-2021",
        "2021-2022",
        "2022-2023",
        "2023-2024"
    ]
    
    # Method 2: Generate seasons automatically
    seasons_auto = generate_season_list(2013, 2025)  # 2013-2014 to 2023-2024
    
    print("Available seasons:")
    for season in seasons_auto:
        print(f"  {season}")
    
    # Choose which seasons to scrape
    seasons_to_scrape = seasons_auto  # or seasons_manual
    
    # Scrape multiple seasons
    print(f"\nStarting to scrape {len(seasons_to_scrape)} seasons...")
    all_seasons_data = scrape_multiple_seasons(base_url, seasons_to_scrape)
    
    if all_seasons_data:
        # Convert to DataFrame
        df_all = pd.DataFrame(all_seasons_data)
        
        print(f"\nTotal records scraped: {len(df_all)}")
        print(f"Seasons covered: {df_all['season'].nunique()}")
        print(f"Teams found: {df_all['team_name'].nunique()}")
        
        # Display sample data
        print("\nSample data:")
        print(df_all[['team_name', 'season', 'adj_gross_gbp']].head(10))
        
        # Save to CSV with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'premier_league_salaries_{timestamp}.csv'
        df_all.to_csv(filename, index=False)
        print(f"\nData saved to {filename}")
        
        # Summary statistics
        print("\nSummary by season:")
        season_summary = df_all.groupby('season').agg({
            'team_name': 'count',
            'adj_gross_gbp': 'sum'
        }).rename(columns={'team_name': 'teams_count', 'adj_gross_gbp': 'total_adj_gross'})
        
        print(season_summary)
        
        # Show top spending teams
        print("\nTop 10 highest spending teams (by adj_gross_gbp):")
        top_spenders = df_all.nlargest(10, 'adj_gross_gbp')[['team_name', 'season', 'adj_gross_gbp']]
        print(top_spenders)
        
        # Show teams that appeared in multiple seasons
        print("\nTeams by season count:")
        team_seasons = df_all['team_name'].value_counts().head(10)
        print(team_seasons)
        
    else:
        print("No data was scraped successfully.")
        
    # Optional: Scrape just specific seasons
    print("\n" + "="*50)
    print("Example: Scraping specific seasons")
    
    specific_seasons = ["2020-2021", "2021-2022", "2022-2023"]
    specific_data = scrape_multiple_seasons(base_url, specific_seasons)
    
    if specific_data:
        df_specific = pd.DataFrame(specific_data)
        print(f"Scraped {len(df_specific)} records from {len(specific_seasons)} seasons")
        print(df_specific[['team_name', 'season', 'adj_gross_gbp']].head())
        
        # Show example of clean integer values
        print("\nExample of clean integer values:")
        print("Newcastle:", df_specific[df_specific['team_name'] == 'Newcastle']['adj_gross_gbp'].iloc[0] if 'Newcastle' in df_specific['team_name'].values else "Not found")
        print("West Bromwich:", df_specific[df_specific['team_name'] == 'West Bromwich']['adj_gross_gbp'].iloc[0] if 'West Bromwich' in df_specific['team_name'].values else "Not found")
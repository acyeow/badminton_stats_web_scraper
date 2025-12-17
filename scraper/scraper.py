from seleniumwire import webdriver
from bs4 import BeautifulSoup
import csv
import time
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from datetime import datetime

from config.scraper_config import RANKINGS_URL, OUTPUT_DIR, EVENT_TYPES

class Scraper:
    def __init__(self, rankings_url: str, output_dir: str, event_types: list):
        options = Options()
        # Set user agent to avoid detection
        options.set_preference("general.useragent.override", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0")
        
        self.driver = webdriver.Firefox(options=options)
        self.driver.implicitly_wait(15)
        self.driver.set_page_load_timeout(60)
        self.rankings_url = rankings_url
        self.output_dir = output_dir
        self.event_types = event_types

    def load_page(self):
        """Load the rankings page initially"""
        try:
            print("Loading rankings page...")
            self.driver.get(RANKINGS_URL)
            time.sleep(3)
            print("✓ Page loaded successfully")
            return True
        except Exception as e:
            print(f"Error loading page: {e}")
            return False

    def scrape_event_type(self, event_type):
        """Scrape data for a specific event type"""
        print(f"\n🎯 Scraping {event_type}...")
        
        try:
            # Wait for the dropdown to be clickable
            wait = WebDriverWait(self.driver, 15)
            
            dropdown = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input.el-input__inner[placeholder='Type']"))
            )
            dropdown.click()
            time.sleep(1)
            
            all_options = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".el-select-dropdown__item"))
            )

            # Filter for visible options
            visible_options = [opt for opt in all_options if opt.is_displayed()]
            print(f"Found {len(visible_options)} visible dropdown options")
            
            clicked = False
            for option in visible_options:
                if event_type in option.text:
                    option.click()
                    print(f"✓ Selected {event_type}")
                    clicked = True
                    break
            
            if not clicked:
                print(f"❌ Could not find option for '{event_type}'")
                return None

            time.sleep(0.5)
            search_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Search')] | //button[contains(@class, 'search')]"))
            )
            search_button.click()
            
            print("Waiting for table to reload...")
            time.sleep(3)
            
            html_data = self.driver.page_source
            return html_data
            
        except Exception as e:
            print(f"Error selecting {event_type}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def close(self):
        """Close the browser"""
        try:
            self.driver.quit()
            print("\n✓ Browser closed")
        except Exception as e:
            print(f"Error closing browser: {e}")

    def extract_player_data(self, soup, event_type):
        """Extract player data from table cells"""
        players = []

        is_doubles = 'Double' in event_type
        
        # Find all table cells
        cells = soup.find_all('td', class_='el-table__cell')
        
        # Group cells by 8 (8 columns per row)
        columns_per_row = 8
        
        for i in range(0, len(cells), columns_per_row):
            row_cells = cells[i:i+columns_per_row]
            
            if len(row_cells) < columns_per_row:
                continue
            
            try:
                # Extract rank (column 2)
                rank_cell = row_cells[1].find('div', class_='cell')
                rank = rank_cell.get_text(strip=True) if rank_cell else ''
                
                # Extract rank change (column 3)
                rank_diff_cell = row_cells[2].find('span', class_='rank-difference')
                rank_change = rank_diff_cell.get_text(strip=True) if rank_diff_cell else ''
                
                # Extract country (column 4)
                country_cell = row_cells[3].find('a', class_='link-type')
                country = country_cell.get_text(strip=True) if country_cell else ''
                
                # Extract player name(s) (column 5)
                player_cell = row_cells[4]
                if is_doubles:
                    # For doubles, extract both player names
                    player_links = player_cell.find_all('a', class_='link-type')
                    if len(player_links) >= 2:
                        player1 = player_links[0].find('span').get_text(strip=True) if player_links[0].find('span') else ''
                        player2 = player_links[1].find('span').get_text(strip=True) if player_links[1].find('span') else ''
                        player_name = f"{player1} / {player2}"
                    elif len(player_links) == 1:
                        # Fallback: try to get the full text which includes both names
                        full_text = player_cell.get_text(strip=True)
                        player_name = full_text
                    else:
                        player_name = ''
                else:
                    # For singles, extract single player name
                    player_link = player_cell.find('a', class_='link-type')
                    if player_link:
                        player_name = player_link.find('span').get_text(strip=True) if player_link.find('span') else ''
                    else:
                        player_name = ''
                
                # Extract points (column 6)
                points_cell = row_cells[5].find('div', class_='cell')
                points = points_cell.get_text(strip=True) if points_cell else ''
                
                # Extract tournaments (column 7)
                tournaments_cell = row_cells[6].find('div', class_='cell')
                tournaments = tournaments_cell.get_text(strip=True) if tournaments_cell else ''
                
                # Extract last update (column 8)
                date_cell = row_cells[7].find('div', class_='cell')
                last_update = date_cell.get_text(strip=True) if date_cell else ''
                
                # Only add if we have at least a rank and player name
                if rank and player_name:
                    players.append({
                        'Rank': rank,
                        'Player Name': player_name,
                        'Country': country,
                        'Points': points,
                        'Tournaments': tournaments,
                        'Last Update': last_update,
                        'Rank Change': rank_change
                    })
            
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue
        
        return players

    def save_to_csv(self, players, event_type):
        """Save player data to CSV file"""
        if not players:
            print("No data to save!")
            return
        
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Create filename with event type and date
        event_name = event_type.lower().replace("'", "").replace(" ", "_")
        filename = f'{event_name}_rankings_{datetime.now().strftime("%Y-%m-%d")}.csv'
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Rank', 'Player Name', 'Country', 'Points', 'Tournaments', 'Last Update', 'Rank Change']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for player in players:
                writer.writerow(player)
        
        print(f"✅ Saved {len(players)} players to {filepath}")

if __name__ == '__main__':
    # Initialize the scraper
    scraper = Scraper(RANKINGS_URL, OUTPUT_DIR, EVENT_TYPES)
    
    try:
        # Load the page once
        if not scraper.load_page():
            print("Failed to load page. Exiting...")
            scraper.close()
            exit(1)
        
        # Scrape all event types
        for event_type in EVENT_TYPES:
            html_data = scraper.scrape_event_type(event_type)
            
            if html_data:
                soup = BeautifulSoup(html_data, 'html.parser')
                players = scraper.extract_player_data(soup, event_type)
                
                # Display first few players
                print(f"📊 Found {len(players)} players")
                if players:
                    print("First 5 players:")
                    for i, player in enumerate(players[:5], 1):
                        print(f"  {i}. {player['Rank']}. {player['Player Name']} ({player['Country']}) - {player['Points']} pts")
                    
                    # Save to CSV
                    scraper.save_to_csv(players, event_type)
                else:
                    print("⚠️  No players found")
            else:
                print(f"❌ Failed to scrape {event_type}")
            
            # Small delay between events
            time.sleep(2)
        
        print("\n✅ All events scraped successfully!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()
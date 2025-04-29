from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import pandas as pd

class MySchemeSeleniumScraper:
    def __init__(self):
        # Set up Chrome options
        chrome_options = Options()
        # Uncomment the line below if you want to run headless
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize the driver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), 
                                      options=chrome_options)
        self.schemes = []
        
    def login(self, username=None, password=None):
        """
        Handle login if credentials are provided
        """
        # You'd need to implement the login flow here if you have credentials
        pass
        
    def scrape_schemes(self, limit=20):
        """
        Scrape the schemes using browser automation
        """
        try:
            # Go to the MyScheme portal
            self.driver.get("https://www.myscheme.gov.in/search")
            time.sleep(5)  # Wait for page to load
            
            # Collect scheme data - you'll need to customize this based on the site structure
            scheme_elements = self.driver.find_elements(By.CSS_SELECTOR, ".scheme-card")[:limit]
            
            for element in scheme_elements:
                scheme_data = {}
                # Extract data from the page - customize these selectors
                scheme_data["title"] = element.find_element(By.CSS_SELECTOR, ".scheme-title").text
                scheme_data["description"] = element.find_element(By.CSS_SELECTOR, ".scheme-desc").text
                # Add more fields as needed
                
                self.schemes.append(scheme_data)
                
            return self.schemes
            
        except Exception as e:
            print(f"Error scraping: {str(e)}")
            return []
            
    def save_to_json(self, filename="myscheme_data.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.schemes, f, ensure_ascii=False, indent=4)
        print(f"Data saved to {filename}")
        
    def save_to_csv(self, filename="myscheme_data.csv"):
        if not self.schemes:
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(self.schemes)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Data saved to {filename}")
        
    def close(self):
        self.driver.quit()

# Usage
if __name__ == "__main__":
    scraper = MySchemeSeleniumScraper()
    # Uncomment and add credentials if available
    # scraper.login(username="your_username", password="your_password")
    schemes = scraper.scrape_schemes(limit=20)
    scraper.save_to_json()
    scraper.save_to_csv()
    scraper.close()
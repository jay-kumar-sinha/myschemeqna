from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time
import json
import pandas as pd
import os

class MySchemeSeleniumScraper:
    def __init__(self):
        # Set up Edge options
        edge_options = Options()
        edge_options.add_argument("--window-size=1920,1080")
        
        # Initialize the Edge driver
        self.driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), 
                                    options=edge_options)
        self.schemes = []
        
    def scrape_schemes(self, limit=20):
        """
        Scrape the schemes using browser automation with debugging
        """
        try:
            print("Opening MyScheme portal...")
            self.driver.get("https://www.myscheme.gov.in/search")
            
            # Wait for the page to load
            print("Waiting for page to load...")
            time.sleep(10)  # Increased wait time for page load
            
            # Take a screenshot to see what we're working with
            screenshot_path = "myscheme_page.png"
            self.driver.save_screenshot(screenshot_path)
            print(f"Saved screenshot to {screenshot_path}")
            
            # Get page source for debugging
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print("Saved page source to page_source.html")
            
            # Try different selectors that might match scheme cards
            possible_selectors = [
                ".scheme-card", 
                ".card", 
                ".scheme-item",
                ".scheme",
                "div[class*='scheme']",
                "div[class*='card']",
                ".list-item",
                ".search-result-item"
            ]
            
            print("Trying to find scheme elements with various selectors...")
            found_elements = False
            used_selector = None
            
            for selector in possible_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    scheme_elements = elements[:limit]
                    found_elements = True
                    used_selector = selector
                    break
            
            if not found_elements:
                print("Could not find any scheme elements with predefined selectors.")
                print("Collecting all div elements to analyze structure...")
                
                # Get all divs that might contain relevant data
                all_divs = self.driver.find_elements(By.TAG_NAME, "div")
                print(f"Found {len(all_divs)} div elements")
                
                # Check the first 10 divs for analysis
                for i, div in enumerate(all_divs[:10]):
                    try:
                        print(f"Div {i} class: {div.get_attribute('class')}")
                        print(f"Div {i} text: {div.text[:100]}..." if len(div.text) > 100 else f"Div {i} text: {div.text}")
                    except:
                        print(f"Could not get attributes for div {i}")
                
                return []
            
            # Process the found elements
            print(f"Processing {len(scheme_elements)} scheme elements...")
            
            for element in scheme_elements:
                scheme_data = {}
                
                # Try to extract scheme title (try multiple possible selectors)
                try:
                    title_selectors = [".scheme-title", ".title", "h3", "h4", ".heading", "[class*='title']"]
                    for title_sel in title_selectors:
                        try:
                            title_elem = element.find_element(By.CSS_SELECTOR, title_sel)
                            scheme_data["title"] = title_elem.text
                            print(f"Found title: {scheme_data['title']}")
                            break
                        except:
                            continue
                            
                    if "title" not in scheme_data:
                        # If no specific title element found, use the element's text
                        scheme_data["title"] = element.text.split('\n')[0]
                        print(f"Using first line as title: {scheme_data['title']}")
                except Exception as e:
                    print(f"Error extracting title: {str(e)}")
                    scheme_data["title"] = "Unknown Title"
                
                # Try to extract description
                try:
                    desc_selectors = [".scheme-desc", ".description", "p", ".details", "[class*='desc']"]
                    for desc_sel in desc_selectors:
                        try:
                            desc_elem = element.find_element(By.CSS_SELECTOR, desc_sel)
                            scheme_data["description"] = desc_elem.text
                            print(f"Found description: {scheme_data['description'][:50]}...")
                            break
                        except:
                            continue
                            
                    if "description" not in scheme_data:
                        # If no specific description element found, use the element's text excluding title
                        text_parts = element.text.split('\n')
                        if len(text_parts) > 1:
                            scheme_data["description"] = '\n'.join(text_parts[1:])
                            print(f"Using remaining text as description: {scheme_data['description'][:50]}...")
                except Exception as e:
                    print(f"Error extracting description: {str(e)}")
                    scheme_data["description"] = "No description available"
                
                # Try to get a URL if there's a link
                try:
                    link = element.find_element(By.TAG_NAME, "a")
                    scheme_data["url"] = link.get_attribute("href")
                    print(f"Found URL: {scheme_data['url']}")
                except:
                    scheme_data["url"] = ""
                
                # Add the scheme to our collection
                if scheme_data.get("title", "").strip():  # Only add if we have at least a title
                    self.schemes.append(scheme_data)
            
            return self.schemes
            
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            return []
            
    def save_to_json(self, filename="myscheme_data.json"):
        if not self.schemes:
            print("No data to save to JSON")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump([], f)
        else:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.schemes, f, ensure_ascii=False, indent=4)
            print(f"Data saved to {filename} ({len(self.schemes)} schemes)")
        
    def save_to_csv(self, filename="myscheme_data.csv"):
        if not self.schemes:
            print("No data to save to CSV")
            pd.DataFrame().to_csv(filename, index=False)
        else:
            df = pd.DataFrame(self.schemes)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Data saved to {filename} ({len(self.schemes)} schemes)")
        
    def close(self):
        self.driver.quit()

# Usage
if __name__ == "__main__":
    scraper = MySchemeSeleniumScraper()
    schemes = scraper.scrape_schemes(limit=20)
    scraper.save_to_json()
    scraper.save_to_csv()
    scraper.close()
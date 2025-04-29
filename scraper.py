import requests
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import re
from tqdm import tqdm

class MySchemePortalScraper:
    def __init__(self):
        self.base_url = "https://www.myscheme.gov.in/search"
        self.api_url = "https://www.myscheme.gov.in/api/v1/schemes"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.schemes = []
        
    def get_scheme_ids(self, limit=200):
        """Get IDs of schemes from main listing page"""
        params = {
            "page": 1,
            "limit": limit,
            "lang": "en"
        }
        
        response = requests.get(self.api_url, params=params, headers=self.headers)
        if response.status_code != 200:
            print(f"Failed to fetch scheme list: {response.status_code}")
            return []
            
        data = response.json()
        return [scheme['id'] for scheme in data.get('data', [])]
    
    def get_scheme_details(self, scheme_id):
        """Get detailed information for a specific scheme"""
        detail_url = f"{self.api_url}/{scheme_id}"
        response = requests.get(detail_url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"Failed to fetch scheme {scheme_id}: {response.status_code}")
            return None
            
        return response.json().get('data', {})
    
    def parse_scheme(self, scheme_data):
        """Parse the scheme data into structured format"""
        if not scheme_data:
            return None
            
        scheme = {
            "id": scheme_data.get('id', ''),
            "name": scheme_data.get('name', ''),
            "description": scheme_data.get('description', ''),
            "ministries": [dept.get('name', '') for dept in scheme_data.get('departments', [])],
            "target_beneficiaries": [],
            "eligibility_criteria": scheme_data.get('eligibility', ''),
            "benefits": scheme_data.get('benefits', ''),
            "application_process": scheme_data.get('howToApply', ''),
            "documents_required": scheme_data.get('documentsRequired', ''),
            "tags": [tag.get('name', '') for tag in scheme_data.get('tags', [])]
        }
        
        # Extract beneficiaries
        for category in scheme_data.get('beneficiaries', []):
            scheme["target_beneficiaries"].extend([ben.get('name', '') for ben in category.get('beneficiaries', [])])
            
        return scheme
    
    def scrape(self, limit=150):
        """Main scraping function"""
        print(f"Fetching schemes from MyScheme portal...")
        scheme_ids = self.get_scheme_ids(limit)
        print(f"Found {len(scheme_ids)} schemes. Getting details...")
        
        for scheme_id in tqdm(scheme_ids):
            # Add delay to avoid rate limiting
            time.sleep(1)
            
            scheme_data = self.get_scheme_details(scheme_id)
            parsed_scheme = self.parse_scheme(scheme_data)
            
            if parsed_scheme:
                self.schemes.append(parsed_scheme)
                
        print(f"Successfully scraped {len(self.schemes)} schemes")
        return self.schemes
        
    def save_to_json(self, filename="myscheme_data.json"):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.schemes, f, ensure_ascii=False, indent=4)
        print(f"Data saved to {filename}")
        
    def save_to_csv(self, filename="myscheme_data.csv"):
        """Save scraped data to CSV file"""
        df = pd.DataFrame(self.schemes)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Data saved to {filename}")

if __name__ == "__main__":
    scraper = MySchemePortalScraper()
    schemes = scraper.scrape(limit=150)  # Aiming for more than 100 schemes
    scraper.save_to_json()
    scraper.save_to_csv()
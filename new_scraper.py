import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# === CONFIGURATION ===
OUTPUT_FILE = 'all_schemes_final.json'
BASE_URL = "https://www.myscheme.gov.in/schemes/{}"

# === Selenium Setup ===
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # run without opening browser
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

# === Function to scrape scheme details ===
def scrape_scheme_details(slug):
    url = BASE_URL.format(slug)
    print(f"🔎 Scraping: {url}")
    try:
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.ID, "eligibility")))
        time.sleep(1)  # slight wait
    except Exception as e:
        print(f"⚠️ Error loading {slug}: {e}")
        return {}

    soup = BeautifulSoup(driver.page_source, "html.parser")

    def get_div_text(div_id):
        div = soup.find('div', id=div_id)
        return div.text.strip() if div and div.text.strip() else "N/A"

    scraped_data = {
        "Slug": slug,
        "Scheme Name": soup.find("h1").text.strip() if soup.find("h1") else "N/A",
        "Ministry/Department": get_div_text("details"),
        "Target Beneficiaries": get_div_text("target-beneficiaries"),
        "Description": get_div_text("description"),
        "Benefits": get_div_text("benefits"),
        "Eligibility Criteria": get_div_text("eligibility"),
        "Application Process": get_div_text("application-process"),
        "Documents Required": get_div_text("documents-required"),
    }

    tags_section = soup.find_all("a", class_="tag-item")
    scraped_data["Tags"] = ', '.join([tag.text.strip() for tag in tags_section]) if tags_section else "N/A"

    return scraped_data

# === Function to save to JSON (append) ===
def save_scheme_data(new_data):
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    existing_data.append(new_data)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved slug '{new_data['Slug']}' to '{OUTPUT_FILE}'")

# === Main Interactive Loop ===
def main():
    print("\n🛠️ Enter slugs one by one. Type 'exit' to stop.\n")
    while True:
        slug = input("Enter scheme slug: ").strip()
        if slug.lower() == "exit":
            break
        if not slug:
            print("⚠️ Empty input, try again.")
            continue

        scheme_data = scrape_scheme_details(slug)
        if scheme_data:
            save_scheme_data(scheme_data)

    driver.quit()
    print("\n👋 Done. Exiting...")

if __name__ == "__main__":
    main()

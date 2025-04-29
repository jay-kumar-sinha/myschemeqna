import requests
import json

# API endpoint and API key
API_URL = "https://api.myscheme.gov.in/search/v4/schemes"
API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"

# "Browser-like" Headers
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                  "AppleWebKit/537.36 (KHTML, like Gecko) " \
                  "Chrome/123.0.0.0 Safari/537.36",
    "Origin": "https://www.myscheme.gov.in",
    "Referer": "https://www.myscheme.gov.in/"
}

# Parameters
params = {
    "lang": "en",
    "q": "[]",
    "keyword": "",
    "sort": "",
    "from": 0,
    "size": 200
}

# Fetching data
response = requests.get(API_URL, headers=headers, params=params)

# Checking if the request was successful
if response.status_code == 200:
    data = response.json()
    schemes = data.get("schemes", [])
    
    # Extracting slugs
    slugs = []
    for scheme in schemes:
        slug = scheme.get("slug")
        if slug:
            slugs.append(slug)
    
    # Saving to JSON file
    with open("scheme_slugs.json", "w") as f:
        json.dump(slugs, f, indent=4)
    
    print(f"✅ Successfully saved {len(slugs)} slugs to scheme_slugs.json")
else:
    print(f"❌ Failed to fetch data: {response.status_code} - {response.text}")

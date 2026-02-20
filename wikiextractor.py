# 1. Document Load
# 2. Parsing
# 3. Extraction
# 4. Transformation

import requests
from bs4 import BeautifulSoup

def get_aircraft_specs(name):
    """
    Scrapes the General Characteristics, Performance, Armament, and Avionics
    sections from a Wikipedia aircraft page.

    Returns a dictionary:
        {
            "title": "<Page Title>",
            "general characteristics": [...],
            "performance": [...],
            "armament": [...],
            "avionics": [...]
        }
    """
    url = f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}"
    headers = {"User-Agent": "AircraftScraper/1 (contact: wtpronk@outlook.com)"}

    # Fetch page
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html.parser")

    # Fetch title
    title_tag = soup.find("span", class_="mw-page-title-main")
    page_title = title_tag.get_text(strip=True) if title_tag else aircraft_name

    # Categories to extract
    categories = ["general characteristics", "performance", "armament", "avionics"]
    specs = {"title": page_title}

    for cat in categories:
        # Find first bold tag with the category name
        bold_tag = soup.find(
            "b",
            string=lambda text: isinstance(text, str) and cat in text.lower()
        )

        if bold_tag:
            # Find the first <ul> after the bold tag
            ul = bold_tag.find_next("ul")
            if ul:
                # Extract all <li> as text
                specs[cat] = [li.get_text(" ", strip=True) for li in ul.find_all("li")]
            else:
                specs[cat] = []  # <ul> not found
        else:
            specs[cat] = []      # bold not found

    return specs

# if __name__ == "__main__":
    aircraft_name = str("tu-28")
    aircraft_specs = get_aircraft_specs(aircraft_name)

    print(f"=== {aircraft_specs['title']} ===\n")
    for category, items in aircraft_specs.items():
        if category == "title":
            continue
        print(f"--- {category.title()} ---")
        if items:
            for item in items:
                print(item)
        else:
            print("No data available")
        print("\n")
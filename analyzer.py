import requests
from bs4 import BeautifulSoup

def fetch_website(url):
    """Fetch a website and return its HTML content."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def analyze_basic_info(response):
    """Extract basic information from website response."""
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Get page title
    title = soup.find('title')
    title_text = title.get_text() if title else "No title found"
    
    # Count elements
    headings = soup.find_all(['h1', 'h2', 'h3'])
    images = soup.find_all('img')
    links = soup.find_all('a')
    
    # Print report
    print("\n=== BASIC ANALYSIS ===")
    print(f"Title: {title_text}")
    print(f"Headings (H1-H3): {len(headings)}")
    print(f"Images: {len(images)}")
    print(f"Links: {len(links)}")        

# Test it
if __name__ == "__main__":
    url = "https://www.wikipedia.org"
    print(f"Fetching {url}...")
    
    response = fetch_website(url)
    
    if response:
        print(f"Success! Status Code: {response.status_code}")
        print(f"Page size: {len(response.content)} bytes")
        analyze_basic_info(response)
    else:
        print("Failed to fetch website")
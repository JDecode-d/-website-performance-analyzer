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

def check_seo_issues(response, url):
    """Check for common SEO problems."""
    soup = BeautifulSoup(response.content, 'html.parser')
    issues = []
    
    # Check meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if not meta_desc:
        issues.append("❌ Missing meta description")
    elif len(meta_desc.get('content', '')) < 50:
        issues.append("⚠️  Meta description too short (should be 50-160 chars)")
    
    # Check title length
    title = soup.find('title')
    if title:
        title_length = len(title.get_text())
        if title_length < 30:
            issues.append(f"⚠️  Title too short ({title_length} chars, should be 30-60)")
        elif title_length > 60:
            issues.append(f"⚠️  Title too long ({title_length} chars, should be 30-60)")
    
    # Check H1 tags
    h1_tags = soup.find_all('h1')
    if len(h1_tags) == 0:
        issues.append("❌ No H1 tag found")
    elif len(h1_tags) > 1:
        issues.append(f"⚠️  Multiple H1 tags found ({len(h1_tags)}), should only have 1")
    
    # Check for HTTPS
    if not url.startswith('https://'):
        issues.append("❌ Not using HTTPS (insecure)")
    
    # Check images without alt text
    images = soup.find_all('img')
    images_without_alt = [img for img in images if not img.get('alt')]
    if images_without_alt:
        issues.append(f"⚠️  {len(images_without_alt)} images missing alt text")
    
    # Print results
    print("\n=== SEO ANALYSIS ===")
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✅ No major SEO issues found")        

# Test it
if __name__ == "__main__":
    url = "https://www.wikipedia.org"
    print(f"Fetching {url}...")
    
    response = fetch_website(url)
    
    if response:
        print(f"Success! Status Code: {response.status_code}")
        print(f"Page size: {len(response.content)} bytes")
        analyze_basic_info(response)
        check_seo_issues(response, url)
    else:
        print("Failed to fetch website")
import requests
from bs4 import BeautifulSoup
import time
import sys
from datetime import datetime

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
    
    # Build report string
    output = ["\n=== BASIC ANALYSIS ==="]
    output.append(f"Title: {title_text}")
    output.append(f"Headings (H1-H3): {len(headings)}")
    output.append(f"Images: {len(images)}")
    output.append(f"Links: {len(links)}")
    
    return "\n".join(output)

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
    
    # Build report
    output = ["\n=== SEO ANALYSIS ==="]
    if issues:
        output.extend(issues)
    else:
        output.append("✅ No major SEO issues found")
    
    return "\n".join(output)

def measure_performance(response):
    """Measure page load performance."""
    output = ["\n=== PERFORMANCE ANALYSIS ==="]
    
    # Page size
    page_size_kb = len(response.content) / 1024
    output.append(f"Page size: {page_size_kb:.2f} KB")
    
    if page_size_kb > 1000:
        output.append("⚠️  Page is very large (>1MB), may load slowly on mobile")
    elif page_size_kb > 500:
        output.append("⚠️  Page is somewhat large (>500KB)")
    else:
        output.append("✅ Page size is reasonable")
    
    # Response time
    load_time = response.elapsed.total_seconds()
    output.append(f"Server response time: {load_time:.2f} seconds")
    
    if load_time > 3:
        output.append("❌ Very slow response time (>3s)")
    elif load_time > 1:
        output.append("⚠️  Slow response time (>1s)")
    else:
        output.append("✅ Fast response time")
    
    return "\n".join(output)

def check_broken_links(soup, base_url):
    """Check for broken internal links."""
    output = ["\n=== LINK ANALYSIS ==="]
    
    links = soup.find_all('a', href=True)
    output.append(f"Total links found: {len(links)}")
    
    # Separate internal and external links
    internal_links = []
    external_links = []
    
    for link in links:
        href = link['href']
        
        # Skip anchors, javascript, mailto, tel
        if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
            continue
        
        # Determine if internal or external
        if href.startswith('http'):
            if base_url in href:
                internal_links.append(href)
            else:
                external_links.append(href)
        else:
            # Relative links are internal
            internal_links.append(href)
    
    output.append(f"Internal links: {len(internal_links)}")
    output.append(f"External links: {len(external_links)}")
    
    # Check for common issues
    if len(internal_links) == 0:
        output.append("⚠️  No internal links found - poor site structure")
    
    if len(external_links) > len(internal_links) * 2:
        output.append("⚠️  Too many external links compared to internal (may hurt SEO)")
    
    return "\n".join(output)

def analyze_images(soup):
    """Analyze image optimization issues."""
    output = ["\n=== IMAGE ANALYSIS ==="]
    
    images = soup.find_all('img')
    output.append(f"Total images: {len(images)}")
    
    if len(images) == 0:
        output.append("ℹ️  No images found on page")
        return "\n".join(output)
    
    issues = []
    
    # Check for missing alt text
    no_alt = [img for img in images if not img.get('alt')]
    if no_alt:
        issues.append(f"⚠️  {len(no_alt)} images missing alt text (accessibility & SEO issue)")
    
    # Check for missing width/height attributes
    no_dimensions = [img for img in images if not (img.get('width') and img.get('height'))]
    if no_dimensions:
        issues.append(f"⚠️  {len(no_dimensions)} images missing width/height (causes layout shift)")
    
    # Check for external images
    external_images = [img for img in images if img.get('src', '').startswith('http')]
    if external_images:
        issues.append(f"ℹ️  {len(external_images)} images loaded from external sources")
    
    # Report findings
    if issues:
        output.extend(issues)
    else:
        output.append("✅ No major image issues found")
    
    return "\n".join(output)

def save_report(url, report_content):
    """Save analysis report to a text file."""
    # Create reports directory if it doesn't exist
    import os
    if not os.path.exists('reports'):
        os.makedirs('reports')
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = url.replace('https://', '').replace('http://', '').split('/')[0]
    filename = f"reports/{domain}_{timestamp}.txt"
    
    # Write report
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n📄 Report saved to: {filename}")
    return filename    

# Test it
if __name__ == "__main__":
    # Check if URL was provided
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <url>")
        print("Example: python analyzer.py https://example.com")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Add https:// if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Build report content
    report = []
    report.append(f"WEBSITE ANALYSIS REPORT")
    report.append(f"Analyzed: {url}")
    report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 50)
    
    response = fetch_website(url)
    
    if response:
        report.append(f"\n✅ Successfully fetched website (Status: {response.status_code})")
        
        # Run analysis and collect results
        soup = BeautifulSoup(response.content, 'html.parser')
        
        report.append(analyze_basic_info(response))
        report.append(check_seo_issues(response, url))
        report.append(measure_performance(response))
        report.append(check_broken_links(soup, url))
        report.append(analyze_images(soup))
        
        report.append("\n" + "=" * 50)
        report.append("Analysis complete!")
        
        # Join all report sections
        full_report = "\n".join(report)
        
        # Print to screen
        print(full_report)
        
        # Save to file
        save_report(url, full_report)
        
    else:
        print("\n❌ Failed to analyze website")
        sys.exit(1)
import requests
from bs4 import BeautifulSoup
import time
import sys
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def colorize(text, color_type):
    """Add color to text based on issue severity."""
    if '❌' in text or 'Very slow' in text or 'Missing' in text:
        return Fore.RED + text + Style.RESET_ALL
    elif '⚠️' in text or 'too short' in text or 'too long' in text:
        return Fore.YELLOW + text + Style.RESET_ALL
    elif '✅' in text:
        return Fore.GREEN + text + Style.RESET_ALL
    elif 'ℹ️' in text:
        return Fore.CYAN + text + Style.RESET_ALL
    else:
        return text

def calculate_score(report_text):
    """Calculate overall performance score based on issues found."""
    score = 100
    
    # Count issue types
    critical_issues = report_text.count('❌')
    warnings = report_text.count('⚠️')
    successes = report_text.count('✅')
    
    # Deduct points
    score -= (critical_issues * 15)  # -15 per critical issue
    score -= (warnings * 5)           # -5 per warning
    
    # Don't go below 0
    score = max(0, score)
    
    # Determine grade
    if score >= 90:
        grade = "A"
        color = Fore.GREEN
    elif score >= 75:
        grade = "B"
        color = Fore.LIGHTGREEN_EX
    elif score >= 60:
        grade = "C"
        color = Fore.YELLOW
    elif score >= 40:
        grade = "D"
        color = Fore.LIGHTYELLOW_EX
    else:
        grade = "F"
        color = Fore.RED
    
    return score, grade, color, critical_issues, warnings, successes

def extract_priority_issues(report_text):
    """Extract and prioritize issues from report."""
    lines = report_text.split('\n')
    
    critical = []
    warnings = []
    
    for line in lines:
        if '❌' in line:
            critical.append(line.strip())
        elif '⚠️' in line:
            warnings.append(line.strip())
    
    # Build priority section
    priority_report = ["\n🚨 PRIORITY ISSUES (Fix These First)"]
    priority_report.append("=" * 50)
    
    if critical:
        priority_report.append("\nCRITICAL:")
        priority_report.extend(critical)
    
    if warnings:
        priority_report.append("\nWARNINGS:")
        priority_report.extend(warnings)
    
    if not critical and not warnings:
        priority_report.append("\n✅ No issues found - site looks good!")
    
    priority_report.append("")
    
    return "\n".join(priority_report)

def fetch_website(url):
    """Fetch a website and return its HTML content."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout:
        print(f"\n❌ Error: Site took too long to respond (>30 seconds)")
        print("   Possible causes: Slow server, heavy traffic, or connectivity issues")
        return None
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Could not connect to {url}")
        print("   Possible causes: Site is down, DNS issues, or network problems")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Error: HTTP {e.response.status_code} - {e.response.reason}")
        if e.response.status_code == 403:
            print("   Site is blocking automated requests (bot protection)")
        elif e.response.status_code == 404:
            print("   Page not found - check the URL")
        elif e.response.status_code == 500:
            print("   Server error - site may be experiencing issues")
        return None
    except requests.exceptions.TooManyRedirects:
        print(f"\n❌ Error: Too many redirects")
        print("   Site has a redirect loop - configuration issue")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error fetching {url}: {e}")
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
        
        # Join all report sections
        full_report = "\n".join(report)
        
        # Calculate score
        score, grade, color, critical, warnings, successes = calculate_score(full_report)
        
        # Add score summary to beginning
        score_summary = [
            "=" * 50,
            f"OVERALL SCORE: {score}/100 (Grade: {grade})",
            f"Critical Issues: {critical} | Warnings: {warnings} | Passed: {successes}",
            "=" * 50
        ]
        
        # Extract priority issues
        priority_section = extract_priority_issues(full_report)
        
        # Combine: score + priority issues + full report
        full_report = "\n".join(score_summary) + priority_section + "\n" + full_report + "\nAnalysis complete!"
        
        # Print with colors
        for line in full_report.split('\n'):
            print(colorize(line, None))
        
        # Save to file
        save_report(url, full_report)
        
    else:
        print("\n❌ Failed to analyze website")
        sys.exit(1)
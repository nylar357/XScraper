import requests
import re
from bs4 import BeautifulSoup, Comment
import argparse
import warnings
from urllib.parse import urljoin

# Suppress only the specific InsecureRequestWarning from urllib3
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

def scrape_target(url, user_agent, timeout, verify_ssl):
    """
    Scrapes a target URL for cybersecurity-relevant information.
    """
    print(f"[*] Scraping target: {url}")
    results = {
        'url': url,
        'headers': {},
        'technologies': set(),
        'server_info': 'Not Detected',
        'comments': [],
        'links': {'internal': set(), 'external': set()},
        'emails': set(),
        'potential_files': set(),
        'meta_generator': None,
        'cookies': {}
    }

    headers = {'User-Agent': user_agent}

    try:
        # Make the request
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            verify=verify_ssl, # WARNING: Disabling SSL verification is insecure!
            allow_redirects=True # Follow redirects to get final page info
            )
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        print(f"[*] Status Code: {response.status_code}")

        # --- 1. Analyze Headers ---
        results['headers'] = dict(response.headers)
        server_header = response.headers.get('Server')
        if server_header:
            results['server_info'] = server_header
            print(f"[+] Server Header: {server_header}")
            # Simple check for common servers (can be expanded)
            if 'apache' in server_header.lower(): results['technologies'].add('Apache')
            if 'nginx' in server_header.lower(): results['technologies'].add('Nginx')
            if 'iis' in server_header.lower(): results['technologies'].add('IIS')
            if 'litespeed' in server_header.lower(): results['technologies'].add('LiteSpeed')

        powered_by = response.headers.get('X-Powered-By')
        if powered_by:
            results['technologies'].add(powered_by)
            print(f"[+] X-Powered-By: {powered_by}")

        aspnet_version = response.headers.get('X-AspNet-Version')
        if aspnet_version:
            results['technologies'].add(f'ASP.NET {aspnet_version}')
            print(f"[+] X-AspNet-Version: {aspnet_version}")

        # Analyze Cookies
        for cookie in response.cookies:
            results['cookies'][cookie.name] = {
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path,
                'secure': cookie.secure,
                'httponly': cookie.has_nonstandard_attr('httponly') or cookie.has_nonstandard_attr('HttpOnly'), # Handle case variations
                'expires': cookie.expires
            }
            # Look for common session cookie patterns
            if 'sess' in cookie.name.lower() or 'sid' in cookie.name.lower():
                 results['technologies'].add('Session Management Cookie Found')
            if 'wp_' in cookie.name.lower() or 'wordpress_' in cookie.name.lower():
                 results['technologies'].add('WordPress (from cookie)')

        # --- 2. Analyze HTML Content (if available) ---
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find Meta Generator Tag (Common in CMS like WordPress, Joomla)
            meta_gen = soup.find('meta', attrs={'name': 'generator'})
            if meta_gen and meta_gen.get('content'):
                results['meta_generator'] = meta_gen['content']
                results['technologies'].add(f"Generator: {meta_gen['content']}")
                print(f"[+] Meta Generator: {meta_gen['content']}")
                if 'wordpress' in meta_gen['content'].lower(): results['technologies'].add('WordPress')
                if 'joomla' in meta_gen['content'].lower(): results['technologies'].add('Joomla')
                if 'drupal' in meta_gen['content'].lower(): results['technologies'].add('Drupal')

            # Find Comments
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                results['comments'].append(comment.strip())
                # Basic check for version info or sensitive keywords in comments
                if re.search(r'version|v\d+\.\d+|debug|config|pass|user', comment, re.IGNORECASE):
                    print(f"[!] Potential sensitive info in comment: {comment[:100].strip()}...")


            # Find Links and potential files/directories
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href) # Resolve relative URLs

                if href.startswith('#') or href.startswith('javascript:'):
                    continue

                if url in full_url:
                    results['links']['internal'].add(full_url)
                    # Look for potentially interesting internal links
                    if any(keyword in href.lower() for keyword in ['admin', 'login', 'wp-admin', 'dashboard', 'config', 'backup', '.zip', '.sql', '.bak', '.git', '.env']):
                         results['potential_files'].add(full_url)
                         print(f"[!] Potential interesting link/file found: {full_url}")
                else:
                    results['links']['external'].add(full_url)

            # Find Script Sources (JS Libraries/Frameworks)
            for script in soup.find_all('script', src=True):
                 src = script['src']
                 if 'jquery' in src.lower(): results['technologies'].add('jQuery')
                 if 'angular' in src.lower(): results['technologies'].add('Angular')
                 if 'react' in src.lower(): results['technologies'].add('React')
                 if 'vue' in src.lower(): results['technologies'].add('Vue.js')
                 # Could add regex for version numbers here

            # Find CSS Links (CSS Frameworks)
            for css in soup.find_all('link', rel='stylesheet', href=True):
                href = css['href']
                if 'bootstrap' in href.lower(): results['technologies'].add('Bootstrap')
                if 'foundation' in href.lower(): results['technologies'].add('Foundation')

            # Find Email Addresses in text
            emails_found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
            for email in emails_found:
                results['emails'].add(email)
                print(f"[+] Email found: {email}")

        else:
            print(f"[*] Content-Type is '{content_type}', not parsing HTML.")


    except requests.exceptions.Timeout:
        print(f"[!] Error: Request timed out after {timeout} seconds.")
        results['error'] = 'Timeout'
    except requests.exceptions.SSLError as e:
        print(f"[!] Error: SSL verification failed: {e}. Try running with --no-verify (use with caution!).")
        results['error'] = f'SSL Error: {e}'
    except requests.exceptions.RequestException as e:
        print(f"[!] Error: An error occurred during the request: {e}")
        results['error'] = str(e)
    except Exception as e:
        print(f"[!] Error: An unexpected error occurred: {e}")
        results['error'] = str(e)

    print("[*] Scraping finished.")
    return results

def print_results(results):
    """Prints the gathered results in a structured format."""
    print("\n" + "="*50)
    print("      RECONNAISSANCE RESULTS")
    print("="*50)
    print(f"Target URL: {results['url']}")


    if results.get('error'):
        print(f"\n--- Error Encountered ---")
        print(results['error'])
        return # Stop printing if there was a major error

    print(f"\n--- Server Information ---")
    print(f"Detected Server: {results['server_info']}")

    if results['technologies']:
        print("\n--- Detected Technologies/Frameworks ---")
        for tech in sorted(list(results['technologies'])):
            print(f"- {tech}")
    else:
        print("\n--- Detected Technologies/Frameworks ---")
        print("None explicitly detected.")

    if results['meta_generator']:
         print(f"\n--- Meta Generator Tag ---")
         print(results['meta_generator'])

    print("\n--- HTTP Headers (Subset) ---")
    # Print only selected interesting headers
    interesting_headers = ['Server', 'X-Powered-By', 'X-AspNet-Version', 'Content-Security-Policy', 'Strict-Transport-Security', 'X-Frame-Options', 'X-Content-Type-Options']
    for header, value in results['headers'].items():
        if header in interesting_headers:
             print(f"{header}: {value}")

    print("\n--- Cookies ---")
    if results['cookies']:
        for name, data in results['cookies'].items():
            flags = []
            if data['secure']: flags.append('Secure')
            if data['httponly']: flags.append('HttpOnly')
            # Could add SameSite check if available in your requests/urllib3 version
            print(f"- {name}: ... (Value Hidden) | Domain={data['domain']} | Path={data['path']} | Flags=[{', '.join(flags)}]")
    else:
        print("No cookies detected in the response.")

    print("\n--- Potential Interesting Links/Files ---")
    if results['potential_files']:
        for link in sorted(list(results['potential_files'])):
            print(f"- {link}")
    else:
        print("None detected.")

    print("\n--- Found Email Addresses ---")
    if results['emails']:
        for email in sorted(list(results['emails'])):
            print(f"- {email}")
    else:
        print("None detected.")

    print("\n--- Comments ---")
    if results['comments']:
        print(f"Found {len(results['comments'])} comments. Potential sensitive ones logged during scan.")
        # Optionally print all comments (can be very verbose)
        for i, comment in enumerate(results['comments']):
             print(f"Comment {i+1}: {comment[:150].strip()}...") # Truncate long comments
    else:
        print("No HTML comments found.")

    print("\n--- Links Found ---")
    print(f"Internal Links: {len(results['links']['internal'])}")
    print(f"External Links: {len(results['links']['external'])}")
    print("="*50 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Basic Web Scraper for Cybersecurity Reconnaissance")
    parser.add_argument("url", help="Target URL (e.g., http://example.com)")
    parser.add_argument("-ua", "--user-agent", default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36", help="User-Agent string for requests")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument("--no-verify", action="store_false", dest="verify_ssl", help="Disable SSL certificate verification (INSECURE!)")

    args = parser.parse_args()

    if not args.verify_ssl:
        print("[WARNING] SSL certificate verification is DISABLED. This is insecure and should only be used if you trust the target server or for specific testing scenarios.")

    if not args.url.startswith(('http://', 'https://')):
        print("[Error] URL must start with http:// or https://")
    else:
        scan_results = scrape_target(args.url, args.user_agent, args.timeout, args.verify_ssl)
        print_results(scan_results)

#!/usr/bin/env python3

# --- Creation ---
# by nylar357
# email :bryce_polymorph@proton.me
# www.linkedin.com/in/brycezg

import argparse
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import dns.resolver
import sys
import socket # For socket.gaierror

# --- Configuration ---
COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop", "ns1", "ns2",
    "ns3", "ns4", "webdisk", "cpanel", "whm", "autodiscover", "autoconfig",
    "msoid", "admin", "api", "dev", "staging", "test", "beta", "vpn", "shop",
    "blog", "news", "support", "helpdesk", "files", "backup", "cloud", "db",
    "sql", "mysql", "mongo", "secure", "owa", "exchange", "portal", "internal",
    "intranet", "git", "svn", "docker", "jenkins", "jira", "wordpress", "wiki", 
    "forum", "webserver", "webserv", "vnc", "upload", "users", "temp", "sqlserver",
    "store", "storage", "sh", "secret", "passwd", "pass", "schedules", "register"
]
REQUEST_TIMEOUT = 10 # seconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
# --- End Configuration ---

# --- Helper Functions ---

def print_info(message):
    print(f"[+] {message}")

def print_warning(message):
    print(f"[!] WARNING: {message}")

def print_error(message):
    print(f"[-] ERROR: {message}", file=sys.stderr)

def print_header(title):
    print("\n" + "=" * 40)
    print(f" {title}")
    print("=" * 40)

def setup_session(proxy_url=None):
    """Creates a requests session with optional proxy support."""
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})

    if proxy_url:
        if not proxy_url.startswith(('http://', 'https://', 'socks5://', 'socks4://')):
             print_warning(f"Proxy URL '{proxy_url}' might be missing scheme (http/https/socks5/socks4). Assuming http.")
             proxy_url = 'http://' + proxy_url # Default assumption

        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        try:
            session.proxies.update(proxies)
            print_info(f"Using proxy: {proxy_url}")
            # Test proxy connection (optional, can slow down startup)
            # print_info("Testing proxy connection...")
            # session.get("https://httpbin.org/ip", timeout=REQUEST_TIMEOUT)
            # print_info("Proxy connection successful.")
        except requests.exceptions.RequestException as e:
            print_error(f"Proxy connection failed: {e}")
            print_warning("Continuing without proxy.")
            session.proxies = {} # Clear proxies if connection failed
        except Exception as e:
             print_error(f"Unexpected error setting up proxy: {e}")
             print_warning("Continuing without proxy.")
             session.proxies = {}
    return session

def get_base_domain(url):
    """Extracts the base domain (e.g., example.com) from a URL."""
    try:
        parsed_url = urlparse(url)
        domain_parts = parsed_url.netloc.split('.')
        # Handle cases like www.example.co.uk -> example.co.uk
        if len(domain_parts) > 2:
             # Basic check for common TLDs, might need refinement for complex cases
             if domain_parts[-2] in ('co', 'com', 'org', 'net', 'gov', 'edu', 'ru', 'by', 'uk', 'de', 'us') and len(domain_parts[-1]) == 2:
                 return '.'.join(domain_parts[-3:])
             else:
                 return '.'.join(domain_parts[-2:])
        return parsed_url.netloc
    except Exception as e:
        print_error(f"Ghostrider! shit is fucked! Could not parse domain from URL '{url}': {e}")
        return None

# --- Scraping Functions ---

def get_server_info(session, url):
    """Retrieves server-related HTTP headers."""
    print_header("Server Information")
    try:
        response = session.head(url, allow_redirects=True, timeout=REQUEST_TIMEOUT)
        print_info(f"Target URL (after redirects): {response.url}")
        print_info(f"Status Code: {response.status_code}")

        headers_to_check = ['Server', 'X-Powered-By', 'X-AspNet-Version', 'Via', 'X-Proxy-ID']
        found_headers = False
        for header in headers_to_check:
            if header in response.headers:
                print_info(f"{header}: {response.headers[header]}")
                found_headers = True

        if not found_headers:
            print_info("No common server identifying headers found.")
        # print("\nFull Headers:")
        # for key, value in response.headers.items():
        #     print(f"  {key}: {value}")

    except requests.exceptions.Timeout:
        print_error(f"Request timed out while fetching headers for {url}")
    except requests.exceptions.RequestException as e:
        print_error(f"Could not fetch headers for {url}: {e}")
    except Exception as e:
        print_error(f"An unexpected error occurred fetching headers: {e}")


def get_robots_txt(session, url):
    """Fetches and displays the content of robots.txt."""
    print_header("Robots.txt")
    robots_url = urljoin(url, '/robots.txt')
    try:
        response = session.get(robots_url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            print_info(f"Found robots.txt at {robots_url}")
            print("-" * 20 + " Content " + "-" * 20)
            print(response.text.strip())
            print("-" * (40 + len(" Content ")))
        elif response.status_code == 404:
            print_info("robots.txt not found (404).")
        else:
            print_warning(f"Received status code {response.status_code} for robots.txt.")

    except requests.exceptions.Timeout:
        print_error(f"Ghostrider! they timed us out while fetching {robots_url}")
    except requests.exceptions.RequestException as e:
        print_error(f"Could not fetch {robots_url}: {e}")
    except Exception as e:
        print_error(f"Ghostrider! an unexpected error occurred fetching robots.txt: {e}")


def find_emails(session, url):
    """Scrapes the main page HTML for email addresses."""
    print_header("Ghostrider We've got Emails Found on Homepage")
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # Regex for finding email addresses (adjust if needed)
        email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = set(re.findall(email_regex, response.text))

        # Alternative: Use BeautifulSoup to avoid emails in JS/CSS comments (can be slower)
        # soup = BeautifulSoup(response.text, 'lxml') # or 'html.parser'
        # text_content = soup.get_text()
        # emails = set(re.findall(email_regex, text_content))


        if emails:
            print_info(f"email search : ghostrider! found {len(emails)} unique potential email address(es):")
            for email in emails:
                print(f"  - {email}")
        else:
            print_info("email search : thats a big negative ghostrider!")

    except requests.exceptions.Timeout:
        print_error(f"Request timed out while fetching homepage {url} for email scraping.")
    except requests.exceptions.HTTPError as e:
         print_error(f"HTTP Error fetching homepage {url}: {e}")
    except requests.exceptions.RequestException as e:
        print_error(f"Could not fetch homepage {url} for email scraping: {e}")
    except Exception as e:
        print_error(f"An unexpected error occurred during email scraping: {e}")


def find_subdomains(domain):
    """Performs basic subdomain enumeration using DNS resolution."""
    if not domain:
        print_error("Cannot perform subdomain enumeration without a valid base domain.")
        return

    print_header(f"Subdomain Enumeration (Basic Check for {domain})")
    found_subdomains = []
    resolver = dns.resolver.Resolver()
    # Optionally configure resolver (e.g., specific nameservers)
    resolver.nameservers = ['1.1.1.1']

    for sub in COMMON_SUBDOMAINS:
        target_subdomain = f"{sub}.{domain}"
        try:
            # Try resolving A records first
            answers = resolver.resolve(target_subdomain, 'A')
            if answers:
                ips = [answer.address for answer in answers]
                print_info(f"Found: {target_subdomain} -> {', '.join(ips)}")
                found_subdomains.append(target_subdomain)
        except dns.resolver.NXDOMAIN:
            # Subdomain does not exist
            pass
        except dns.resolver.NoAnswer:
            # Exists but no A record (might have CNAME, MX etc.)
            try:
                 # Check for CNAME specifically
                 cname_answers = resolver.resolve(target_subdomain, 'CNAME')
                 if cname_answers:
                     cname_target = cname_answers[0].target.to_text()
                     print_info(f"Found: {target_subdomain} -> CNAME {cname_target}")
                     found_subdomains.append(target_subdomain)
                 else:
                      print_info(f"Found: {target_subdomain} (exists but no A or CNAME record found)")
                      found_subdomains.append(target_subdomain)
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.Timeout):
                 pass # Ignore if CNAME check also fails
            except Exception as e:
                 print_warning(f"Error resolving CNAME for {target_subdomain}: {e}")
        except dns.exception.Timeout:
            print_warning(f"DNS query timed out for {target_subdomain}")
        except dns.resolver.NoNameservers as e:
            print_error(f"DNS resolution failed for {target_subdomain}: No nameservers available - {e}")
            break # Stop if nameservers fail
        except socket.gaierror as e:
             print_error(f"Network error during DNS resolution for {target_subdomain}: {e}")
        except Exception as e:
            # Catch other potential DNS errors
            print_warning(f"An unexpected DNS error occurred for {target_subdomain}: {e}")

    if not found_subdomains:
        print_info("No common subdomains resolved.")
    else:
         print_info(f"Finished checking {len(COMMON_SUBDOMAINS)} common subdomains. Found {len(found_subdomains)}.")
    print_info("Note: This is NOT an exhaustive subdomain search.")


# --- Main Execution ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Reconnaissance Scraper for Security Audits.")
    parser.add_argument("url", help="Target URL (e.g., https://example.com)")
    parser.add_argument("-p", "--proxy", help="Proxy URL (e.g., http://127.0.0.1:8080 or socks5://127.0.0.1:9050)", default=None)
    # parser.add_argument("-w", "--wordlist", help="Wordlist file for more extensive subdomain bruteforcing (optional)") # Example for future extension

    args = parser.parse_args()

    target_url = args.url
    # Ensure URL has a scheme
    if not target_url.startswith(('http://', 'https://')):
        print_warning("URL missing scheme (http/https). Assuming https.")
        target_url = 'https://' + target_url

    print_info(f"Starting reconnaissance on: {target_url}")

    # Setup session (handles proxy)
    session = setup_session(args.proxy)

    # --- Perform Recon Tasks ---
    get_server_info(session, target_url)
    get_robots_txt(session, target_url)
    find_emails(session, target_url)

    base_domain = get_base_domain(target_url)
    if base_domain:
        find_subdomains(base_domain)
    else:
        print_error("Could not determine base domain. Skipping subdomain enumeration.")

    print("\nReconnaissance complete.")

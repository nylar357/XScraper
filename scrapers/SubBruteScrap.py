import argparse
import os
import socket
import subprocess
import requests
# --- Creation ---
# by nylar357
# email :bryce_polymorph@proton.me
# www.linkedin.com/in/brycezg

def find_subdomains(domain):
    """
    Finds subdomains of a given domain using a brute-force approach.
    """
    subdomains = []
    common_subdomains = [
        "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop", "ns1", "ns2", "admin",
        "cpanel", "webdisk", "autodiscover", "autoconfig", "msoid", "sip", "lyncdiscover",
        "enterpriseenrollment", "enterpriseregistration", "owa", "portal", "vpn", "test"
    ]

    print("\n--- Finding Subdomains ---")
    for subdomain in common_subdomains:
        full_domain = f"{subdomain}.{domain}"
        try:
            # Resolve the domain name
            socket.gethostbyname(full_domain)
            print(f"[+] Found: {full_domain}")
            subdomains.append(full_domain)
        except socket.gaierror:
            # Could not resolve the domain name
            pass
    
    print("--- Subdomain Scan Complete ---")
    return subdomains

def port_scan(domain):
    """
    Performs a port scan on the given domain using nmap.
    """
    print("\n--- Port Scanning ---")
    try:
        # Run nmap with -F (fast scan) and -T4 (aggressive timing)
        result = subprocess.run(
            ["nmap", "-A", "-p-", "-T4", domain, "--open"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
    except FileNotFoundError:
        print("nmap is not installed. Please install it to use this feature.")
    except subprocess.CalledProcessError as e:
        print(f"Error running nmap: {e.stderr}")
    print("--- Port Scan Complete ---")

def analyze_web_services(domain, subdomains):
    """
    Analyzes web services running on the domain and subdomains.
    """
    print("\n--- Web Service Analysis ---")
    targets = [domain] + subdomains
    for target in targets:
        for protocol in ["http", "https"]:
            url = f"{protocol}://{target}"
            try:
                response = requests.get(url, timeout=5)
                print(f"\n[+] Analysis for {url}")
                if "server" in response.headers:
                    print(f"  - Server: {response.headers['server']}")
                if "x-powered-by" in response.headers:
                    print(f"  - X-Powered-By: {response.headers['x-powered-by']}")
            except requests.exceptions.RequestException as e:
                # print(f"Could not connect to {url}: {e}")
                pass
    print("--- Web Service Analysis Complete ---")

def dir_bruteforce(url, wordlist):
    """
    Performs a directory and file brute-force attack.
    """
    print(f"\n--- Brute Forcing Directories and Files on {url} ---")
    for word in wordlist:
        word = word.strip()
        full_url = f"{url}/{word}"
        try:
            response = requests.get(full_url, timeout=5)
            if response.status_code == 200:
                print(f"[+] Found: {full_url}")
        except requests.exceptions.RequestException:
            pass
    print("--- Brute Force Complete ---")

def main():
    parser = argparse.ArgumentParser(description="Domain Scanner")
    parser.add_argument("domain", help="The domain to scan")
    parser.add_argument("--wordlist", help="Path to a wordlist file for directory brute-forcing")
    args = parser.parse_args()

    print(f"Scanning {args.domain}...")
    
    found_subdomains = find_subdomains(args.domain)
    print(f"\nFound {len(found_subdomains)} subdomains.")

    port_scan(args.domain)
    
    analyze_web_services(args.domain, found_subdomains)

    if args.wordlist:
        try:
            with open(args.wordlist, "r") as f:
                wordlist = f.readlines()
        except FileNotFoundError:
            print(f"Wordlist file not found: {args.wordlist}")
            wordlist = []
    else:
        wordlist = ["admin", "login", "dashboard", "wp-admin", "test"]

    if wordlist:
        targets = [args.domain] + found_subdomains
        for target in targets:
            for protocol in ["http", "https"]:
                url = f"{protocol}://{target}"
                dir_bruteforce(url, wordlist)


if __name__ == "__main__":
    main()

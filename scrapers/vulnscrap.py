#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import subprocess
import argparse
import sys
import re
import json
from urllib.parse import urlparse, urlunparse
import shutil  # To check if searchsploit exists

# --- Creation ---
# by nylar357
# email :bryce_polymorph@proton.me
# www.linkedin.com/in/brycezg

# --- Configuration ---
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
DEFAULT_TIMEOUT = 10  # seconds

# --- Helper Functions ---


def check_searchsploit_installed():
    """Checks if the searchsploit command is available in the system PATH."""
    return shutil.which("searchsploit") is not None


def normalize_url(url):
    """Adds http:// if scheme is missing."""
    parsed = urlparse(url)
    if not parsed.scheme:
        # Assume http if no scheme is provided
        parsed = parsed._replace(scheme="http")
    return urlunparse(parsed)


def fetch_website_data(url, user_agent, timeout):
    """Fetches website HTML content and headers."""
    print(f"[*] Fetching data from: {url}")
    headers = {"User-Agent": user_agent}
    try:
        response = requests.get(
            url, headers=headers, timeout=timeout, allow_redirects=True, verify=True
        )  # Added verify=True for good practice
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        print(f"[*] Successfully fetched (Status Code: {response.status_code})")
        return response.headers, response.text
    except requests.exceptions.Timeout:
        print(f"[!] Timeout error while connecting to {url}", file=sys.stderr)
    except requests.exceptions.SSLError as e:
        print(
            f"[!] SSL Error connecting to {url}: {e}. Trying with verify=False (use with caution).",
            file=sys.stderr,
        )
        try:
            # Retry without SSL verification - POTENTIALLY INSECURE
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
                verify=False,
            )
            response.raise_for_status()
            print(
                f"[*] Successfully fetched with verify=False (Status Code: {response.status_code})"
            )
            return response.headers, response.text
        except requests.exceptions.RequestException as retry_e:
            print(
                f"[!] Error fetching {url} even with verify=False: {retry_e}",
                file=sys.stderr,
            )
    except requests.exceptions.RequestException as e:
        print(f"[!] Error fetching {url}: {e}", file=sys.stderr)
    return None, None


def identify_services(headers, html_content):
    """Identifies potential services/technologies from headers and HTML content."""
    services = set()
    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Check Server Header
    server = headers.get("Server")
    if server:
        # Basic cleanup: remove detailed version numbers for broader search
        server_name = server.split("/")[0].split(" ")[0]  # e.g. Apache/2.4.1 -> Apache
        if server_name:
            print(f"[*] Found Server header: {server}")
            services.add(server_name.lower())  # Use lower case for consistency

    # 2. Check X-Powered-By Header
    powered_by = headers.get("X-Powered-By")
    if powered_by:
        # Basic cleanup
        powered_by_name = powered_by.split("/")[0].split(" ")[0]  # e.g. PHP/7.4 -> PHP
        if powered_by_name:
            print(f"[*] Found X-Powered-By header: {powered_by}")
            services.add(powered_by_name.lower())

    # 3. Check common Meta Generators (CMS/Framework indicators)
    generator_tag = soup.find("meta", attrs={"name": re.compile(r"^generator$", re.I)})
    if generator_tag and generator_tag.get("content"):
        generator = generator_tag["content"].strip()
        # Basic cleanup
        generator_name = generator.split(" ")[0]  # e.g. "WordPress 5.8" -> "WordPress"
        if generator_name:
            print(f"[*] Found meta generator tag: {generator}")
            services.add(generator_name.lower())

    # 4. (Optional) Add more checks here:
    #    - Look for specific script paths (e.g., /wp-content/ indicates WordPress)
    #    - Look for specific comments left by frameworks
    #    - Check cookies set by the server (e.g., `phpsessid`) - requires inspecting response.cookies

    print(
        f"[*] Identified potential services: {', '.join(services) if services else 'None'}"
    )
    return list(services)  # Return as list for iteration


def search_exploitdb(service_name):
    """Searches Exploit-DB using searchsploit for a given service name."""
    print(f"\n--- Searching Exploit-DB for: {service_name} ---")
    command = ["searchsploit", "--nocolor", "-j", service_name]  # -j for JSON output


try:
    # Set encoding explicitly if needed, though text=True usually handles it
    result = subprocess.run(
        command, capture_output=True, text=True, check=False, encoding="utf-8"
    )

    if result.returncode != 0:
        # Searchsploit often returns non-zero if no results are found.
        # Check stderr for actual errors.
        if "command not found" in result.stderr.lower():
            print(
                f"[!] Error: 'searchsploit' command not found. Is exploitdb installed and in PATH?",
                file=sys.stderr,
            )
            return None  # Indicate critical error
        elif (
            result.stderr and "database needs update" not in result.stderr.lower()
        ):  # Ignore update warnings
            print(
                f"[!] Searchsploit error (stderr):\n{result.stderr.strip()}",
                file=sys.stderr,
            )
        # If stdout is empty or indicates no results, it's not a script error
        if not result.stdout or '"RESULTS_EXPLOIT": []' in result.stdout:
            print("[-] No potential exploits found in Exploit-DB.")
            return []
        else:
            print(f"[+] Found {len(exploits)} potential exploits:")
            found_exploits = []
            for exploit in exploits:
                title = exploit.get("Title", "N/A")
                edb_id = exploit.get("EDB-ID", "N/A")
                path = exploit.get("Path", "N/A")
                print(f"  - Title: {title} (EDB-ID: {edb_id})")
                # print(f"    Path: {path}") # Optionally print local path
                found_exploits.append({"title": title, "id": edb_id, "path": path})
            return found_exploits  # Return list of dicts

except json.JSONDecodeError:
    print(f"[!] Failed to parse searchsploit JSON output.", file=sys.stderr)
    print(
        f"Raw output:\n{result.stdout[:500]}..."
    )  # Print beginning of output for debugging
    return None  # Indicate parsing error

except FileNotFoundError:
    print(
        f"[!] Error: 'searchsploit' command not found. Is exploitdb installed and in PATH?",
        file=sys.stderr,
    )
    return None  # Indicate critical error
except Exception as e:
    print(
        f"[!] An unexpected error occurred running searchsploit: {e}", file=sys.stderr
    )
    return None  # Indicate critical error
# --- Main Execution ---


def main():
    parser = argparse.ArgumentParser(
        description="Scrape website for services and check Exploit-DB using searchsploit."
    )
    parser.add_argument("url", help="Target URL (e.g., http://example.com)")
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "-ua",
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help="User-Agent string for requests",
    )
    parser.add_argument(
        "--no-exploitdb", action="store_true", help="Skip the Exploit-DB check"
    )

    args = parser.parse_args()

    # Check for searchsploit early if needed
    if not args.no_exploitdb and not check_searchsploit_installed():
        print(
            "[!] Critical Error: 'searchsploit' command not found. Please install exploitdb.",
            file=sys.stderr,
        )
        print(
            "    Installation (Debian/Ubuntu): sudo apt update && sudo apt install exploitdb"
        )
        print("    Don't forget to update: searchsploit -u")
        sys.exit(1)

    target_url = normalize_url(args.url)

    headers, html_content = fetch_website_data(
        target_url, args.user_agent, args.timeout
    )

    if not html_content:
        print("[!] Failed to retrieve website content. Exiting.", file=sys.stderr)
        sys.exit(1)

    identified_services = identify_services(headers if headers else {}, html_content)

    if not args.no_exploitdb:
        if not identified_services:
            print("\n[*] No specific services identified to check against Exploit-DB.")
        else:
            all_exploits = {}
            for service in identified_services:
                # Basic check to avoid overly generic searches if needed
                if len(service) < 3:  # Skip very short names like 'go' unless intended
                    print(
                        f"\n--- Skipping potentially generic search for: {service} ---"
                    )
                    continue

                exploit_results = search_exploitdb(service)
                if exploit_results is None:
                    print(
                        f"[!] Error occurred during searchsploit execution for '{service}'. Cannot proceed reliably.",
                        file=sys.stderr,
                    )
                    # Decide whether to exit or continue with other services
                    # sys.exit(1) # Option: Exit on first searchsploit error
                elif exploit_results:
                    all_exploits[service] = exploit_results

            print("\n--- Summary ---")
            if all_exploits:
                for service, exploits in all_exploits.items():
                    print(
                        f"[+] {service.capitalize()}: Found {len(exploits)} potential exploits."
                    )
            else:
                print(
                    "[-] No potential exploits found for the identified services in Exploit-DB."
                )

    print("\n[*] Scan finished.")
    print(
        "\n[!] Disclaimer: This script is for educational purposes only. "
        "Unauthorized scanning or exploitation of websites is illegal and unethical. "
        "Always obtain explicit permission before scanning any system you do not own."
    )


if __name__ == "__main__":
    main()

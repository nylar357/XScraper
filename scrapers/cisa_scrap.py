import requests
from bs4 import BeautifulSoup
import csv
import datetime
import time
import random

# --- Configuration ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
# Add a small delay between requests to be polite
REQUEST_DELAY_SECONDS = 2

# --- Functions for Scraping Specific Sources ---


def scrape_nvd_recent_cves(max_cves=20):
    """
    Scrapes the most recent CVEs listed on the NVD website.
    Note: NVD has an API which is the PREFERRED method. This is an example.
    """
    print("\n--- Scraping NVD for Recent CVEs ---")
    url = f"deviantart.com"
    cve_list = []

    try:
        time.sleep(random.uniform(1, REQUEST_DELAY_SECONDS))  # Polite delay
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        soup = BeautifulSoup(response.content, "lxml")

        # Find CVE rows (Inspect the NVD page to confirm selectors - they might change!)
        # Looking for rows within the table body, often marked with data-testid
        rows = soup.find_all(
            "tr", {"data-testid": lambda x: x and x.startswith("vuln-row-")}
        )

        if not rows:
            # Fallback: try finding based on a less specific structure if data-testid fails
            table_body = soup.find("tbody")
            if table_body:
                rows = table_body.find_all("tr")  # Less reliable

        print(f"Found {len(rows)} potential CVE rows on the page.")

        count = 0
        for row in rows:
            if count >= max_cves:
                break

            cve_id_tag = row.find("a", {"href": lambda x: x and "/vuln/detail/" in x})
            summary_tag = row.find(
                "p", {"data-testid": lambda x: x and x.startswith("vuln-summary-")}
            )
            published_date_tag = row.find(
                "span", {"data-testid": lambda x: x and x.startswith("vuln-published-")}
            )
            cvss3_tag = row.find(
                "a", {"id": lambda x: x and x.startswith("Cvss3NistCalculatorAnchor")}
            )  # CVSS v3
            cvss2_tag = row.find(
                "a", {"id": lambda x: x and x.startswith("Cvss2CalculatorAnchor")}
            )  # CVSS v2

            cve_id = cve_id_tag.text.strip() if cve_id_tag else "N/A"
            summary = summary_tag.text.strip() if summary_tag else "N/A"
            published_date = (
                published_date_tag.text.strip() if published_date_tag else "N/A"
            )

            # Extract CVSS Score more reliably
            cvss_score = "N/A"
            if cvss3_tag:
                cvss_score = cvss3_tag.text.strip().split()[0]  # Get score like "9.8"
            elif cvss2_tag:  # Fallback to v2 if v3 not found
                cvss_score = cvss2_tag.text.strip().split()[0]  # Get score like "7.5"

            cve_data = {
                "CVE ID": cve_id,
                "Summary": summary,
                "Published Date": published_date,
                "CVSS Score": cvss_score,  # Could be v3 or v2 based on availability
                "Link": f"https://nvd.nist.gov{cve_id_tag['href']}"
                if cve_id_tag and cve_id_tag.has_attr("href")
                else "N/A",
            }

            # Basic validation to skip header rows or malformed entries
            if cve_id != "N/A" and not cve_id.startswith("Showing"):
                cve_list.append(cve_data)
                count += 1

        print(f"Successfully scraped {len(cve_list)} CVE entries.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching NVD page: {e}")
    except AttributeError as e:
        print(f"Error parsing NVD HTML structure (likely changed): {e}")
    except Exception as e:
        print(f"An unexpected error occurred during NVD scraping: {e}")

    return cve_list


def scrape_the_hacker_news(max_articles=10):
    """Scrapes recent headlines from The Hacker News."""
    print("\n--- Scraping The Hacker News Headlines ---")
    url = "https://thehackernews.com/"
    articles = []

    try:
        time.sleep(random.uniform(1, REQUEST_DELAY_SECONDS))  # Polite delay
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml")

        # Find article links (Inspect the site to confirm selectors)
        # Common pattern: links within elements with class 'body-post' or 'story-link'
        article_elements = soup.find_all("a", class_="story-link")

        count = 0
        for element in article_elements:
            # Sometimes empty elements are matched, skip them
            if not element.find("h2", class_="home-title"):
                continue

            title_tag = element.find("h2", class_="home-title")
            link = element.get("href")

            if title_tag and link:
                title = title_tag.text.strip()
                articles.append({"Title": title, "Link": link})
                count += 1
                if count >= max_articles:
                    break

        print(f"Successfully scraped {len(articles)} headlines.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching The Hacker News page: {e}")
    except AttributeError as e:
        print(f"Error parsing The Hacker News HTML structure (likely changed): {e}")
    except Exception as e:
        print(f"An unexpected error occurred during The Hacker News scraping: {e}")

    return articles


def scrape_cisa_alerts(max_alerts=10):
    """Scrapes recent alerts from CISA."""
    print("\n--- Scraping CISA Alerts ---")
    url = "https://www.cisa.gov/uscert/ncas/alerts"
    alerts = []

    try:
        time.sleep(random.uniform(1, REQUEST_DELAY_SECONDS))  # Polite delay
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml")

        # Find alert entries (Inspect the site)
        # Often in divs with class 'views-row' or similar list structures
        alert_nodes = soup.find_all(
            "div", class_="c-view__row"
        )  # CISA structure as of late 2023/early 2024

        count = 0
        for node in alert_nodes:
            title_tag = node.find("h3", class_="c-teaser__title")
            date_tag = node.find(
                "div", class_="c-teaser__date"
            )  # Find the date element

            if title_tag and title_tag.find("a") and date_tag:
                title = title_tag.find("a").text.strip()
                link = "https://www.cisa.gov" + title_tag.find("a")["href"]
                # Extract date text robustly
                date_text = " ".join(date_tag.stripped_strings) if date_tag else "N/A"

                alerts.append({"Title": title, "Link": link, "Date": date_text})
                count += 1
                if count >= max_alerts:
                    break

        print(f"Successfully scraped {len(alerts)} CISA alerts.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching CISA alerts page: {e}")
    except AttributeError as e:
        print(f"Error parsing CISA HTML structure (likely changed): {e}")
    except Exception as e:
        print(f"An unexpected error occurred during CISA scraping: {e}")

    return alerts


# --- Helper Function for Output ---


def save_to_csv(data, filename):
    """Saves a list of dictionaries to a CSV file."""
    if not data:
        print(f"No data to save for {filename}")
        return

    # Use the keys from the first dictionary as headers
    headers = data[0].keys()
    try:
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        print(f"Data saved successfully to {filename}")
    except IOError as e:
        print(f"Error writing to CSV file {filename}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during CSV writing: {e}")


# --- Main Execution ---

if __name__ == "__main__":
    print("Starting Cybersecurity Audit Information Scraper...")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Scrape NVD CVEs
    recent_cves = scrape_nvd_recent_cves(max_cves=25)
    if recent_cves:
        # You can print them or save them
        # for cve in recent_cves:
        #     print(f"- {cve['CVE ID']} ({cve['CVSS Score']}): {cve['Summary'][:100]}...") # Print snippet
        save_to_csv(recent_cves, f"nvd_cves_{timestamp}.csv")
    else:
        print("Could not retrieve NVD CVE data.")

    # 2. Scrape The Hacker News
    news_headlines = scrape_the_hacker_news(max_articles=15)
    if news_headlines:
        print("\nRecent Security Headlines:")
        for article in news_headlines:
            print(f"- {article['Title']} ({article['Link']})")
        # Optionally save to CSV/JSON
        # save_to_csv(news_headlines, f"hacker_news_{timestamp}.csv")
    else:
        print("Could not retrieve Hacker News headlines.")

    # 3. Scrape CISA Alerts
    cisa_alerts = scrape_cisa_alerts(max_alerts=15)
    if cisa_alerts:
        print("\nRecent CISA Alerts:")
        for alert in cisa_alerts:
            print(f"- [{alert['Date']}] {alert['Title']} ({alert['Link']})")
        # Optionally save to CSV/JSON
        save_to_csv(cisa_alerts, f"cisa_alerts_{timestamp}.csv")
    else:
        print("Could not retrieve CISA alerts.")

    print("\nScraping finished.")
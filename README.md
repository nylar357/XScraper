# XScraper - Recon Web Scraper

## New Release: `1shot.sh` - Rapid Reconnaissance and Asset Discovery
*(Legacy script XScrap remains available - Reconnoitre with your web scraper!)*

[![Watch the video](img/1shot.png)](https://youtu.be/mkibO3xbN1w)

A suite of tools—now featuring `1shot.sh`—designed to gather publicly available information from specified web sources for cybersecurity intelligence, threat monitoring, and open-source intelligence (OSINT) gathering.

**Disclaimer:** This tool is intended for **educational and ethical purposes only**. Ensure you have explicit permission before scraping any website, respect `robots.txt`, and comply with all applicable laws and terms of service. The developers assume no liability and are not responsible for any misuse or damage caused by this tool.

---

## Table of Contents

- [Description](#description)
- [Purpose](#purpose)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Ethical Considerations](#ethical-considerations)
- [Contributing](#contributing)
- [License](#license)

---

## Description

This project provides configurable tools focused on extracting data relevant to cybersecurity professionals. 

The primary focus of this repository is now **`1shot.sh`**, a brand-new script designed for rapid, single-execution reconnaissance. It seamlessly strings together Project Discovery tools to map out target surfaces rapidly and efficiently without complex configurations.

The suite can still be adapted to monitor various online sources for indicators of compromise (IoCs), mentions of vulnerabilities, or other security-related keywords and patterns using the legacy Python scripts.

![preview](img/1shot_large.png)

## Purpose

In the realm of cybersecurity, staying informed about emerging threats, vulnerabilities, and potential exposures is crucial. This tool aims to automate the collection of publicly accessible data from pre-defined sources to aid in:

*   **Automated Reconnaissance:** Quickly chaining CLI tools for immediate attack surface mapping and asset discovery.
*   **Threat Intelligence:** Identifying discussions or posts related to new threats, malware, or attack vectors.
*   **Vulnerability Monitoring:** Tracking mentions of specific CVEs or software weaknesses.
*   **OSINT Gathering:** Collecting public information related to specific domains, IPs, or organizations.

## Features

**New `1shot.sh` Capabilities:**
*   **High-Speed Execution:** Leverages `subfinder`, `httpx`, `katana`, and `naabu` to map out target surfaces efficiently.
*   **Optional Vulnerability Scanning:** Seamlessly integrates `Nuclei` for targeted, immediate vulnerability scanning directly within the workflow.
*   **Streamlined Extraction:** Automates the parsing of key web elements directly in your terminal.

**Legacy `XScrap` Capabilities:**
*   Allows for proxy usage, user agent customizing, web service enumeration, scraps robots.txt, site related emails, and sub-domain enumeration.
*   Searches for user-defined keywords, regular expressions, or patterns (e.g., CVE IDs, email formats, specific terms).
*   Extracts relevant text snippets or data points associated with matches.

## Technology Stack

*   **Core Reconnaissance:** Bash, Project Discovery tools (`subfinder`, `httpx`, `katana`, `naabu`, `nuclei`).
*   **Language:** Python 3.x (for legacy scraper).
*   **Core Libraries (Python):** `requests`, `BeautifulSoup4` or `lxml`, `dnspython`, `PySocks`.

## Installation

1.  **Clone the repository:**
    ```bash                                                                                                       
    git clone [https://github.com/nylar357/XScraper.git](https://github.com/nylar357/XScraper.git)                                                                                    
    cd XScraper                                                                                        
    ``` 
2.  **Install Project Discovery Dependencies (for `1shot.sh`):**
    Ensure you have Go installed, or download the pre-compiled binaries for `subfinder`, `httpx`, `katana`, `naabu`, and `nuclei` from the Project Discovery GitHub repository. Add them to your system path.
3.  **Install Python Dependencies (for legacy scripts):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install bs4 dnspython lxml PySocks requests
    ```

## Usage

**Primary Usage: `1shot.sh`**
Run the streamlined reconnaissance script directly against your authorized target:
```bash
./1shot.sh <target_domain>
```
## Ethical Considerations

**Using this tool responsibly is paramount.**

    Legality & Permissions: Only scrape websites where you have explicit permission or where the robots.txt file permits scraping the intended sections. Always comply with the website's Terms of Service. Scraping private forums or restricted areas is illegal and unethical.

    Server Load: Implement significant delays between requests (time.sleep()). Do not overload the target servers. Set a descriptive and truthful User-Agent string that allows website administrators to identify your bot.

    Data Privacy: Be extremely cautious when searching for or handling potentially sensitive information (PII, credentials). Do not collect, store, or distribute private data found inadvertently. Focus on publicly acknowledged threats and vulnerabilities.

    Purpose: Use the gathered information ethically for defensive cybersecurity purposes only. Do not use it to facilitate unauthorized access, harassment, or any illegal activities.

### Misuse of this tool can lead to legal consequences and blocking of your IP address 

#### Contributing

##### Contributions are welcome! If you'd like to improve the scraper, please follow these steps:

    Fork the repository.

    Create a new branch (git checkout -b feature/YourFeatureName).

    Make your changes.

    Commit your changes (git commit -m 'Add some feature').

    Push to the branch (git push origin feature/YourFeatureName).

    Open a Pull Request.

License

This project is licensed under the MIT License - see the LICENSE file for details.

#!/bin/bash

# USAGE: ./1shot.sh <INPUT>
# Example: ./1shot.sh example.com

if [ -z "$1" ]; then
    echo "Usage: $0 <INPUT_DOMAIN_OR_IP>"
    echo "Example: $0 example.com"
    exit 1
fi

# Clean TARGET: strip protocol (http:// or https://), trailing path, and port
TARGET=$(echo "$1" | sed -e 's|^[^/]*//||' -e 's|/.*||' -e 's|:[0-9]*$||')
DATE=$(date +%F)
WORKSPACE="recon_${TARGET}_${DATE}"

# --- PRE-FLIGHT CHECK ---
# Check if the 'httpx' in path is the correct one (ProjectDiscovery)
if ! httpx -version 2>&1 | grep -q "projectdiscovery"; then
    echo "ERROR: The 'httpx' command in your path does not appear to be the ProjectDiscovery version."
    echo "You might have the Python 'httpx' library installed."
    echo "Please ensure ~/go/bin/httpx is in your PATH or alias it."
    exit 1
fi
# ------------------------

# Robust permissions and fallback workspace handling
if [ -d "$WORKSPACE" ] && [ ! -w "$WORKSPACE" ]; then
    echo "[-] WARNING: Default workspace directory '$WORKSPACE' is not writable (owned by root?)."
    WORKSPACE="${WORKSPACE}_$(whoami)"
fi

echo "[+] Creating workspace: $WORKSPACE"
mkdir -p "$WORKSPACE"
cd "$WORKSPACE" || exit

# 1. Input Detection & Initial Discovery
if [[ "$TARGET" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "[+] Input detected as IP address."
    echo "$TARGET" > targets.txt
else
    echo "[+] Input detected as Domain."
    echo "[+] Running Subfinder..."
    subfinder -d "$TARGET" -all -silent > targets.txt
fi

# Fallback check to ensure we always scan at least the main target
if [ ! -s targets.txt ]; then
    echo "$TARGET" > targets.txt
else
    if ! grep -Fxq "$TARGET" targets.txt; then
        echo "$TARGET" >> targets.txt
    fi
fi

echo "[+] Target list created: $(wc -l < targets.txt) assets found."

# 2. Port Scanning (Naabu)
echo "[+] Running Naabu (Port Scan)..."
naabu -list targets.txt -c 50 -rate 1000 -silent > open_ports.txt

if [ ! -s open_ports.txt ]; then
    echo "[-] No open ports found. Exiting."
    exit 1
fi

# 3. HTTP Service Discovery (httpx)
# FIX: Ensure we are using the correct flags for the Go version
echo "[+] Running httpx (Web Service Probe)..."
cat open_ports.txt | httpx -silent -title -tech-detect -status-code -json -o web_assets.json

# Extract URLs for the next step
if [ -f web_assets.json ] && [ -s web_assets.json ]; then
    cat web_assets.json | jq -r '.url' > live_urls.txt
else
    touch live_urls.txt
fi

echo "[+] Web assets identified: $(wc -l < live_urls.txt)"

# Initialize crawled_endpoints.txt and final_scan_list.txt
touch crawled_endpoints.txt final_scan_list.txt

# 4. Spidering & Crawling (Katana)
if [ -s live_urls.txt ]; then
    # FIX: Added 'all' argument to -kf flag
    echo "[+] Running Katana (Crawler)..."
    katana -list live_urls.txt -jc -kf all -silent -o crawled_endpoints.txt

    # Combine base URLs and crawled endpoints
    cat live_urls.txt crawled_endpoints.txt 2>/dev/null | sort -u > final_scan_list.txt
else
    echo "[-] Skipping crawler step: No live web assets found."
fi

# 5. Vulnerability Scanning (Nuclei)
#if [ -s live_urls.txt ]; then
#    echo "[+] Running Nuclei (Vulnerability Scan -- Also FIXED!)..."
#    nuclei -l live_urls.txt \
#        -severity low,medium,high,critical \
#        -etags fuzz,dast,sqli,xss,bruteforce \
#        -stats -je vulnerabilities.json
#fi

# 6. Reporting
echo "-------------------------------------------------------"
echo "Reconnaissance Complete."
echo "Summary:"
echo " - Subdomains/Assets: $(wc -l < targets.txt)"
echo " - Open Ports:        $(wc -l < open_ports.txt)"
echo " - Live Web Servers:  $(wc -l < live_urls.txt)"
echo " - Crawled Endpoints: $(wc -l < crawled_endpoints.txt)"
# Check if file exists before grepping to avoid errors
if [ -f vulnerabilities.json ]; then
    echo " - Vulnerabilities:   $(grep -c "template-id" vulnerabilities.json)"
else
    echo " - Vulnerabilities:   0"
fi
echo "-------------------------------------------------------"
echo "Data stored in: $PWD"

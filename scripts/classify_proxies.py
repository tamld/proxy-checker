import os
import requests
import geoip2.database
from dotenv import load_dotenv

# Load environment variables from .env
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(ENV_PATH)

# API Keys and file paths from environment variables
IPINFO_API_KEY = os.getenv("IPINFO_API_KEY")
PROXYCHECK_API_KEY = os.getenv("PROXYCHECK_API_KEY")

BASE_PATH = os.getenv("BASE_PATH", os.path.join(PROJECT_ROOT, "data"))
LIVE_PROXIES_FILE = os.getenv("LIVE_PROXIES_FILE", os.path.join(BASE_PATH, "output/live_proxies.txt"))
RESIDENTIAL_PROXIES_FILE = os.getenv("RESIDENTIAL_PROXIES_FILE", os.path.join(BASE_PATH, "output/residential_proxies.txt"))
CHECKED_PROXIES_FILE = os.getenv("CHECKED_PROXIES_FILE", os.path.join(BASE_PATH, "output/checked_proxies.txt"))
ASN_DB_PATH = os.getenv("ASN_DB_PATH", os.path.join(BASE_PATH, "geolite/GeoLite2-ASN.mmdb"))
ASN_DB_URL = os.getenv("ASN_DB_URL", "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-ASN.mmdb")

# Function to download GeoLite2 ASN database if not already downloaded
def download_db(url, save_path):
    if not os.path.exists(save_path):
        print(f"Downloading {url} to {save_path}...")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded {url} successfully.")
        except requests.RequestException as e:
            print(f"Failed to download {url}: {e}")
            exit(1)
    else:
        print(f"{save_path} already exists, skipping download.")

# Function to extract IP from a proxy string
def extract_ip(proxy):
    """
    Extracts the IP address from a proxy string in the format:
    - protocol://ip:port or ip:port
    """
    # Remove protocol part if it exists
    if "://" in proxy:
        proxy = proxy.split("://")[1]

    # Extract the IP part from the remaining string
    ip = proxy.split(":")[0]
    return ip

# Function to classify proxies using GeoLite2 ASN Database
def classify_proxy_asn(ip):
    try:
        reader = geoip2.database.Reader(ASN_DB_PATH)
        response = reader.asn(ip)
        asn = response.autonomous_system_number
        asn_org = response.autonomous_system_organization

        # Basic classification based on ASN organization name
        if "Hosting" in asn_org or "Data Center" in asn_org or "Cloud" in asn_org:
            print(f"IP {ip} classified as Datacenter based on ASN ({asn}, {asn_org}).")
            return "Datacenter"
        else:
            print(f"IP {ip} may be Residential based on ASN ({asn}, {asn_org}).")
            return "Potentially Residential"
    except geoip2.errors.AddressNotFoundError:
        print(f"ASN data not found for IP {ip}.")
        return "Unknown"
    except Exception as e:
        print(f"Error getting ASN for IP {ip}: {e}")
        return "Unknown"

# Function to classify proxies using IPInfo API
def classify_proxy_by_ipinfo(ip):
    print(f"Classifying IP {ip} using IPInfo API...")
    url = f"https://ipinfo.io/{ip}?token={IPINFO_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        ip_type = data.get("type", "Unknown")
        if ip_type.lower() == "residential":
            print(f"IP {ip} classified as Residential.")
            return "Residential"
        else:
            print(f"IP {ip} classified as Datacenter.")
            return "Datacenter"
    except requests.RequestException:
        print(f"Error calling IPInfo API for IP {ip}")
        return "Unknown"

# Function to check risk level of the proxy using ProxyCheck.io API
def check_proxy_risk(proxy):
    ip = extract_ip(proxy)
    print(f"Checking risk level of IP {ip} using ProxyCheck.io API...")
    url = f"http://proxycheck.io/v2/{ip}?key={PROXYCHECK_API_KEY}&vpn=1&asn=1&risk=2&port=1"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if ip in data:
            risk_score = data[ip].get('risk', 100)
            print(f"Risk score for IP {ip}: {risk_score}")
            return risk_score
    except requests.RequestException:
        print(f"Error calling ProxyCheck API for IP {ip}")
    return None

# Main function to classify proxies
def classify_proxies():
    # Download necessary databases
    download_db(ASN_DB_URL, ASN_DB_PATH)

    residential_proxies = []
    checked_proxies = []

    # Load live proxies from file
    try:
        with open(LIVE_PROXIES_FILE, "r") as file:
            live_proxies = [line.strip() for line in file if line.strip()]
            print(f"Loaded {len(live_proxies)} live proxies from {LIVE_PROXIES_FILE}.")
    except FileNotFoundError:
        print(f"Error: {LIVE_PROXIES_FILE} not found.")
        return

    # Classify proxies
    for proxy in live_proxies:
        print(f"\nProcessing proxy: {proxy}")
        ip = extract_ip(proxy)

        # Step 1: Classify the proxy using GeoLite2 ASN Database
        asn_classification = classify_proxy_asn(ip)
        if asn_classification == "Datacenter":
            continue  # Skip proxies that are classified as datacenter

        # Step 2: Use IPInfo API for further classification if ASN was inconclusive
        if asn_classification == "Unknown" or asn_classification == "Potentially Residential":
            proxy_type = classify_proxy_by_ipinfo(ip)
        else:
            proxy_type = asn_classification

        if proxy_type == "Residential":
            residential_proxies.append(proxy)
            print(f"Proxy {proxy} added to residential list.")

        # Step 3: Check the risk level using ProxyCheck.io for further filtering
        risk_score = check_proxy_risk(proxy)
        if risk_score is not None and risk_score <= 50:
            checked_proxies.append(proxy)
            print(f"Proxy {proxy} added to checked (safe) list.")

    # Save residential proxies to file
    with open(RESIDENTIAL_PROXIES_FILE, "w") as res_file:
        for proxy in residential_proxies:
            res_file.write(f"{proxy}\n")
    print(f"Saved {len(residential_proxies)} residential proxies to {RESIDENTIAL_PROXIES_FILE}.")

    # Save checked proxies to file
    with open(CHECKED_PROXIES_FILE, "w") as chk_file:
        for proxy in checked_proxies:
            chk_file.write(f"{proxy}\n")
    print(f"Saved {len(checked_proxies)} checked (safe) proxies to {CHECKED_PROXIES_FILE}.")

    # Print final classification counts
    print("\n=== Classification Summary ===")
    print(f"Total Residential Proxies: {len(residential_proxies)}")
    print(f"Checked (Safe) Proxies: {len(checked_proxies)}")

if __name__ == "__main__":
    classify_proxies()
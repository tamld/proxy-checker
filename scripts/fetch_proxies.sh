#!/bin/bash

# Get the current directory of the script
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

# Load environment variables from .env file in the project root
set -o allexport
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
else
    echo ".env file not found at $PROJECT_ROOT! Please create a .env file with necessary configuration."
    exit 1
fi
set +o allexport

# Check if BASE_PATH is set
if [ -z "$BASE_PATH" ]; then
    echo "BASE_PATH is not set in the .env file. Exiting..."
    exit 1
fi

# Define the list of proxy URLs categorized by type automatically
PROXY_URLS=(
    # HTTP Proxies
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt"
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt"
    # HTTPS Proxies
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/https_proxies.txt"
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt"
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt"
    # SOCKS4 Proxies
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt"
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt"
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks4.txt"
    # SOCKS5 Proxies
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt"
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt"
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks5.txt"
    # Others
    "https://rootjazz.com/proxies/proxies.txt"
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/xResults/Proxies.txt"
)

# Categorize URLs automatically by checking their content
HTTP_URLS=()
HTTPS_URLS=()
SOCKS4_URLS=()
SOCKS5_URLS=()
UNKNOWN_URLS=()

for url in "${PROXY_URLS[@]}"; do
    if [[ $url == *"socks5"* ]]; then
        SOCKS5_URLS+=("$url")
    elif [[ $url == *"socks4"* ]]; then
        SOCKS4_URLS+=("$url")
    elif [[ $url == *"https"* ]]; then
        HTTPS_URLS+=("$url")
    elif [[ $url == *"http"* ]]; then
        HTTP_URLS+=("$url")
    else
        UNKNOWN_URLS+=("$url")
    fi
done

# Output file where all proxies will be saved (values from .env)
OUTPUT_FILE="${PROXIES_FILE:-${BASE_PATH}/input/proxies.txt}"
TEMP_FILE="${BASE_PATH}/temp_proxies.txt"
UNREACHABLE_FILE="${BASE_PATH}/unreachable_urls.txt"

# Remove old output files if they exist
rm -f "$OUTPUT_FILE" "$TEMP_FILE" "$UNREACHABLE_FILE"

# Function to check if a URL is reachable
check_url() {
    local url=$1
    if curl --output /dev/null --silent --head --fail --max-time 5 "$url"; then
        return 0 # URL is reachable
    else
        echo "$url" >> "$UNREACHABLE_FILE"
        return 1 # URL is not reachable
    fi
}

# Function to fetch proxies from a given URL
fetch_proxies() {
    local url=$1
    local prefix=$2
    if check_url "$url"; then
        echo "Fetching proxies from $url"
        # Fetch proxies and add the prefix for protocol (http, https, socks4, socks5)
        curl -s --max-time 5 "$url" | grep -Eo '((socks4|socks5|https|http)://)?([0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}' | sed -E "s/^([0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}$/$prefix\:\/\/&/" >> "$TEMP_FILE"
    else
        echo "Skipping unreachable URL: $url"
    fi
}

# Remove duplicate URLs before fetching to avoid redundant work
HTTP_URLS=($(printf "%s\n" "${HTTP_URLS[@]}" | sort -u))
HTTPS_URLS=($(printf "%s\n" "${HTTPS_URLS[@]}" | sort -u))
SOCKS4_URLS=($(printf "%s\n" "${SOCKS4_URLS[@]}" | sort -u))
SOCKS5_URLS=($(printf "%s\n" "${SOCKS5_URLS[@]}" | sort -u))
UNKNOWN_URLS=($(printf "%s\n" "${UNKNOWN_URLS[@]}" | sort -u))

# Fetch proxies in parallel using xargs for each type
export -f fetch_proxies
export -f check_url
export TEMP_FILE
export UNREACHABLE_FILE

# Fetch HTTP proxies
printf "%s\n" "${HTTP_URLS[@]}" | xargs -P 10 -I {} bash -c 'fetch_proxies "$@"' _ "{}" "http"

# Fetch HTTPS proxies
printf "%s\n" "${HTTPS_URLS[@]}" | xargs -P 10 -I {} bash -c 'fetch_proxies "$@"' _ "{}" "https"

# Fetch SOCKS4 proxies
printf "%s\n" "${SOCKS4_URLS[@]}" | xargs -P 10 -I {} bash -c 'fetch_proxies "$@"' _ "{}" "socks4"

# Fetch SOCKS5 proxies
printf "%s\n" "${SOCKS5_URLS[@]}" | xargs -P 10 -I {} bash -c 'fetch_proxies "$@"' _ "{}" "socks5"

# Fetch UNKNOWN proxies as HTTP by default
printf "%s\n" "${UNKNOWN_URLS[@]}" | xargs -P 10 -I {} bash -c 'fetch_proxies "$@"' _ "{}" "http"

# Remove empty lines and invalid entries, ensure final format is correct
sort -u "$TEMP_FILE" | grep -E '^(socks4|socks5|https|http)://([0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}$' > "$OUTPUT_FILE"

# Remove temporary file
rm -f "$TEMP_FILE"

# Print a message indicating the script has completed
echo "Proxies have been saved to $OUTPUT_FILE"
echo "Unreachable URLs have been saved to $UNREACHABLE_FILE (if any)"

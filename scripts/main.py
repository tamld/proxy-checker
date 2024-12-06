import os
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables from .env
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(ENV_PATH)

# Define paths for bash and Python scripts
FETCH_PROXIES_SCRIPT = os.path.join(SCRIPT_DIR, "fetch_proxies.sh")
DOCKER_PROXY_CHECK_SCRIPT = os.path.join(SCRIPT_DIR, "docker_proxy_check.sh")
CLASSIFY_PROXIES_SCRIPT = os.path.join(SCRIPT_DIR, "classify_proxies.py")
SEND_TELEGRAM_SCRIPT = os.path.join(SCRIPT_DIR, "send_to_telegram.py")

# Define paths for files
BASE_PATH = os.getenv("BASE_PATH", os.path.join(PROJECT_ROOT, "data"))
LIVE_PROXIES_FILE = os.getenv("LIVE_PROXIES_FILE", os.path.join(BASE_PATH, "output/live_proxies.txt"))
RESIDENTIAL_PROXIES_FILE = os.getenv("RESIDENTIAL_PROXIES_FILE", os.path.join(BASE_PATH, "output/residential_proxies.txt"))
CHECKED_PROXIES_FILE = os.getenv("CHECKED_PROXIES_FILE", os.path.join(BASE_PATH, "output/checked_proxies.txt"))
INPUT_PROXIES_FILE = os.path.join(BASE_PATH, "input/proxies.txt")

# Utility function to execute a command in the shell and handle errors
def execute_command(command, description=""):
    """
    Executes a command in the shell and handles errors.
    Args:
        command (str): The command to execute.
        description (str): A description of the task being executed.
    """
    try:
        print(f"Executing: {description if description else command}")
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout.decode())  # Log output from the command
    except subprocess.CalledProcessError as e:
        print(f"Error during {description if description else 'command'}: {e.stderr.decode()}")
        sys.exit(1)

# Function to ensure that required directories exist
def ensure_directories_exist():
    """
    Ensure that all required directories exist. If not, create them.
    """
    directories_to_check = [
        os.path.join(BASE_PATH, "output"),
        os.path.join(BASE_PATH, "geolite"),
        os.path.join(BASE_PATH, "input")
    ]

    print("\nStep 0: Ensuring necessary directories exist...")
    
    for directory in directories_to_check:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"Created directory: {directory}")
            except OSError as e:
                print(f"Error creating directory {directory}: {e}")
                sys.exit(1)

# Function to clean up old proxy files
def cleanup():
    """
    Clean up old proxy files to ensure a fresh start for the next crontab run.
    """
    print("\nStep 5: Cleaning up old proxy files...")

    # Remove output proxy files
    for file_path in [LIVE_PROXIES_FILE, RESIDENTIAL_PROXIES_FILE, CHECKED_PROXIES_FILE]:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted old file: {file_path}")

    # Also remove input proxy file
    if os.path.exists(INPUT_PROXIES_FILE):
        os.remove(INPUT_PROXIES_FILE)
        print(f"Deleted old file: {INPUT_PROXIES_FILE}")

# Main workflow
def main():
    ensure_directories_exist()

    cleanup()

    print("\nStep 1: Fetching proxies...")
    execute_command(f"bash {FETCH_PROXIES_SCRIPT}", description="fetching proxies")

    print("\nStep 2: Checking live proxies using Docker...")
    execute_command(f"bash {DOCKER_PROXY_CHECK_SCRIPT}", description="checking live proxies with Docker")

    print("\nStep 3: Classifying proxies...")
    execute_command(f"python3 {CLASSIFY_PROXIES_SCRIPT}", description="classifying proxies")

    print("\nStep 4: Sending results via Telegram...")
    execute_command(f"python3 {SEND_TELEGRAM_SCRIPT}", description="sending results via Telegram")

    print("\nWorkflow completed successfully.")

if __name__ == "__main__":
    main()

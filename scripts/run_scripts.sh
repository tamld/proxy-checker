#!/bin/bash

# Navigate to the project directory where the scripts are located
cd /root/proxy-checker/scripts

# Activate the Python virtual environment
# Make sure to specify the correct path to the 'venv' folder in your project
source /root/proxy-checker/venv/bin/activate

# Run the main Python script
python3 main.py

# Deactivate the virtual environment after the script execution (optional)
deactivate

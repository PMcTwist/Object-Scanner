#!/bin/bash

# Path to your virtual environment and Python script
VENV_PATH="/home/maynard/scanner_venv"  # Adjust this to your venv location
PYTHON_SCRIPT="/home/maynard/Desktop/Python UI/scanner.py"  # Adjust this to your script's location

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Run the Python script
python "$PYTHON_SCRIPT"

# Optional: Deactivate the virtual environment (not necessary since it will exit after script execution)
deactivate


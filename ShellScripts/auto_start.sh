#!/bin/bash

# Path to Scanner Root file
FILE="../scanner.py"

# Check if the file exists
if [ ! -f "$FILE" ]; then
    echo "Error: File $FILE does not exist."
    exit 1
fi

# Run the Python script
python3 "$FILE"

#!/bin/bash

# Check if two arguments (files) are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <file1> <file2>"
    exit 1
fi

file1="$1"
file2="$2"

# Check if files exist
if [ ! -f "$file1" ] || [ ! -f "$file2" ]; then
    echo "Error: One or both files do not exist."
    exit 1
fi

# Compute SHA256 hashes
hash1=$(sha256sum "$file1" | cut -d ' ' -f1)
hash2=$(sha256sum "$file2" | cut -d ' ' -f1)

# Compare hashes
if [ "$hash1" = "$hash2" ]; then
    echo "Hashes match. Files are identical."
else
    echo "Hashes differ. Files are different."
    echo "Hash of $file1: $hash1"
    echo "Hash of $file2: $hash2"
fi

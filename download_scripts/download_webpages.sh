#!/bin/bash

# Check if exactly one argument is provided
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <path-to-file>"
  exit 1
fi

input_file="$1"

# Verify that the input file exists
if [ ! -f "$input_file" ]; then
  echo "Error: File '$input_file' not found."
  exit 1
fi

# Ensure the downloads directory exists
mkdir -p ../data/downloads

# Read each line from the provided file
while IFS= read -r line
do
  # Prepend the URL
  url="https://minecraft.wiki/w/$line"

  # Create a filename from the line, replacing spaces with underscores and removing special characters
  filename=$(echo "$line" | sed 's/[^a-zA-Z0-9_]/_/g' | tr -d ' ')

  # Check if the file exists and if its size is larger than 1KB (1024 bytes)
  if [ -f "../data/downloads/$filename.html" ]; then
    filesize=$(stat -c%s "../data/downloads/$filename.html")
    if [ "$filesize" -gt 1024 ]; then
      echo "File downloads/$filename.html already exists and is larger than 1KB. Skipping $url."
      continue
    fi
  fi

  # Download the webpage
  wget -q "$url" -O "../data/downloads/$filename.html"
  echo "Downloaded $url to ../data/downloads/$filename.html"
done < "$input_file"

echo "Finished downloading webpages from $input_file."

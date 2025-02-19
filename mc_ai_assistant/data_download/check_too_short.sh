#!/bin/bash

# Use the provided directory or default to the current directory
target_dir="${1:-.}"

# Verify that the target is a directory
if [ ! -d "$target_dir" ]; then
  echo "Error: '$target_dir' is not a valid directory."
  exit 1
fi

# Loop through all regular files in the target directory
for file in "$target_dir"/*; do
  if [ -f "$file" ]; then
    line_count=$(wc -l < "$file")
    if [ "$line_count" -lt 30 ]; then
      echo "$file"
    fi
  fi
done

#!/bin/bash

# Loop through all .md files
find . -type f -name "*.md" -print0 | while IFS= read -r -d '' file; do
    # Check if the file exists
    if [ -e "$file" ]; then
        # Use perl to remove whitespaces between $ and $ and replace the original file
        perl -i -pe 's/\$\s*(.*?)\s*\$/\$$1\$/g' "$file"
    fi
done

echo "Modified all .md files to remove whitespaces"
echo "Running pandoc..."

# Find all .md files (except README.md or readme.md) in subdirectories
find . -type f -name "*.md" ! -iname "README.md" ! -iname "readme.md" -print0 |
while IFS= read -r -d '' file; do
    # Get the filename without extension
    img=$(basename "$file" .md)

    # Check if ${img}.png exists in the same directory
    if [ ! -f "$(dirname "$file")/${img}.png" ]; then
        # Run the pandoc command
        pandoc -o "$(dirname "$file")/${img}.pdf" "$file"
    fi
done

echo "Pandoc finished runing"
echo "Converting pdf to png..."

# Find all .pdf files in subdirectories
find . -type f -name "*.pdf" -print0 | while IFS= read -r -d '' file; do
    # Get the filename without extension
    img=$(basename "$file" .pdf)

    # Check if ${img}.png exists in the same directory
    if [ ! -f "$(dirname "$file")/${img}.png" ]; then
        # Run the convert command
        # pdfcrop --margins "0 0 0 0" input.pdf temp.pdf
        # convert -density 300 -trim temp.pdf output.png
        # rm temp.pdf
        
        # pdfcrop --margins "0 0 0 0" "$file" "$file"
        convert -density 300 -trim "$file" "$(dirname "$file")/${img}.png"
        # rm "$file"
    fi
done

echo "Converted all pdf files to png"


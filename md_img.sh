#!/bin/bash

echo "Removing whitespaces in .md files..."

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
        pandoc -V pagestyle:empty -o "$(dirname "$file")/${img}.pdf" "$file"
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
        convert -define colorspace:auto-grayscale=false --pdf-engine=xelatex -background white -alpha remove -alpha off -density 300 -trim "$file" "$(dirname "$file")/${img}.png"
        rm "$file"
    fi
done

echo "Converted all pdf files to png"
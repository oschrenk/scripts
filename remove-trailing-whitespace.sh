#!/bin/sh

# Remove trailing whitespace of text files in directory
find . -type f -name "*.txt" -exec sh -c 'for i;do sed 's/[[:space:]]*$//' "$i">/tmp/.$$ && mv /tmp/.$$ "$i";done' arg0 {} +
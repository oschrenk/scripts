#!/bin/bash

for file in $(ls ls */xml/*.xml)
do
	echo "Formatting $file"
	xmllint --format $file -o $file
done

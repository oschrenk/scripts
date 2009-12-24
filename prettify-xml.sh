#!/bin/bash

for file in $(ls *.xml)
do
	echo "Formatting $file"
	xmllint --format $file -o $file
done

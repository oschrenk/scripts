#!/bin/sh

echo "" > output-raw.txt

for url in `cat load-test-urls.txt`
do
   curl -K load-test-config.txt $url >> output-raw.txt
done

echo "" > output-processed.txt

sort load-test-urls.txt | uniq | while read line
do
   grep $line output-raw.txt >> output-processed.txt
done

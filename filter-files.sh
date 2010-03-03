#!/bin/sh

# Usage $ filter-files phrase-to-use-as-filter

for f in *
do
 if [ -n "`grep $1 $f`" ]
 then
   cp $f temp/
 fi
done
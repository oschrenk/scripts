#!/bin/sh


for i in *
do

filename=$i

YEAR=${filename:0:2}
MONTH=${filename:3:2}
DAY=${filename:6:2}

ENTRYDATE=$MONTH/$DAY/$YEAR

echo $filename
dayone -d="$ENTRYDATE" new < "$i"

done
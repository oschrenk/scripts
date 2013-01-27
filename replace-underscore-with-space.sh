#!/bin/sh

ls *_* | while read -r FILE
do
  mv "$FILE" "`echo "$FILE" | tr '_' ' '`"
done
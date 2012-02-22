#!/usr/bin/env bash
# taken from http://technicalpickles.com/posts/creating-a-svn-authorsfile-when-migrating-from-subversion-to-git/
# Run this inside an subversion checkout. It outputs a template for the
# svn.authorsfile to the console, so you just need to paste it into a 
# document, and fill in the names and email address for your authors.
authors=$(svn log -q | grep -e '^r' | awk 'BEGIN { FS = "|" } ; { print $2 }' | sort | uniq)
for author in ${authors}; do
  echo "${author} = NAME <USER@DOMAIN>";
done
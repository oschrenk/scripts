#!/usr/bin/env bash
# taken from http://technicalpickles.com/posts/creating-a-svn-authorsfile-when-migrating-from-subversion-to-git/
# Run this inside an subversion checkout. It outputs a template for the
# svn.authorsfile to the console, so you just need to paste it into a 
# document, and fill in the names and email address for your authors.
#
# Usage example: svnauthors.sh http://company.com/repo
authors=$(svn log -q $@ | grep -e '^r[0-9]' | awk 'BEGIN { FS = "|" } ; { print $2 } $1 ~ /r([0-9]+000)/ { print "fetched revision " substr($1, 2) > "/dev/stderr" }' | sort | uniq) 
for author in ${authors}; do
  echo "${author} = NAME <USER@DOMAIN>";
done
#!/bin/bash

names="
App Store
Automator
Calculator
Calendar
Cog
Contacts
Dashboard
Dictionary
Gimp
Google Chrome
iPhoto
iTunes
LibreOffice
Mail
MPlayerX
Preview
Sublime Text 2
The Unarchiver
VLC
"

tmp=/tmp/$(uuidgen)
mdfind -onlyin / 'kMDItemContentType==com.apple.application-bundle' > $tmp
echo "$names" | sed 's/^/\//g;s/$/.app/g;s/ /\\ /g' | xargs -L 1 -J '{}' grep -m 1 -i -F '{}' $tmp | sed 's/ /\\ /g' | xargs mdls -name kMDItemCFBundleIdentifier | sed 's/.*= "\(.*\)"$/\1/'
rm $tmp
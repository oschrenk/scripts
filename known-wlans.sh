#!/bin/sh

defaults read /Library/Preferences/SystemConfiguration/com.apple.airport.preferences RememberedNetworks | egrep -o '(SSID_STR|_timeStamp).+' | sed 's/^.*= \(.*\);$/\1/' | sed 's/^"\(.*\)"$/\1/' | sed 's/\([0-9]\{4\}-..-..\).*/\1/'
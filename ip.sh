#!/bin/bash

# Use privoxy+tor 
# export http_proxy=http://127.0.0.1:8118/

while :
do
	curl -s checkip.dyndns.org|sed -e 's/.*Current IP Address: //' -e 's/<.*$//'
	sleep 120
done
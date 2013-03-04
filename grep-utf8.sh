#!/bin/bash

# Normally you would
# grep --color='auto' -P -n "[\x80-\xFF]" $1

# but OS X uses BSD grep so it doesn't support PCRE ("Perl-compatible
# regular expressions")
# Alternative is to `brew install pcre` which gives you
pcregrep --color='auto' -n "[\x80-\xFF]" $1
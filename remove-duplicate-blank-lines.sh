#!/bin/bash

# Reduces two or more consecutive blank lines to a single blank line

awk '/^$/{ if (! blank++) print; next } { blank=0; print }' $1 > $1.old; rm $1; mv $1.old $1;
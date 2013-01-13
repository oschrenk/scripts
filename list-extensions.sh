#!/bin/sh

# on non mac-systems 'sed -rn'
find . -type f | sed -En 's|.*/[^/]+\.([^/.]+)$|\1|p' | sort -u
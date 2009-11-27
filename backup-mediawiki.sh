#! /bin/sh

site=wiki.host.tld
topurl=http://$site

backupdir=~/Downloads/mirrors/$site

httrack -%i -w $topurl/index.php/Special:Allpages \
-O "$backupdir" -%P -N0 -s0 -p7 -S -a -K0 -%k -A25000 \
-F "Mozilla/4.5 (compatible; HTTrack 3.0x; Windows 98)" \
-%s -x -%x -%u \
"-$site/index.php/Special:*" \
"-$site/index.php?title=Special:*" \
"+$site/index.php/Special:Recenthanges" \
"+*.css" \
"-$site/index.php?title=*&oldid=*" \
"-$site/index.php?title=*&action=edit" \
"-$site/index.php?title=*&curid=*" \
"+$site/index.php?title=*&action=history" \
"-$site/index.php?title=*&action=history&*" \
"-$site/index.php?title=*&curid=*&action=history*" \
"-$site/index.php?title=*&limit=*&action=history"

for page in $(grep "link updated: $site/index.php/" $backupdir/hts-log.txt | sed "s,^.*link updated: $site/index.php/,," | sed ’s/ ->.*//’ | grep -v Special:)
do
wget -nv -O $backupdir/$site/index.php/${page}_raw.txt "$topurl/index.php?index=$page&action=raw"
done
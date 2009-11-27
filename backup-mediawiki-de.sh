#! /bin/sh

# Inspired by blogpost from http://www-public.it-sudparis.eu/~berger_o/weblog/2008/05/30/offline-backup-mediawiki-with-httrack/

site=www.host.tld
topurl=http://$site

backupdir=~/Downloads/mirrors/$site

httrack -%i -w $topurl/Spezial:Alle_Seiten \
-O "$backupdir" -%P -N0 -s0 -p7 -S -a -K0 -%k -A25000 \
-F "Mozilla/4.5 (compatible; HTTrack 3.0x; Windows 98)" \
-%s -x -%x -%u \
"-$site/Spezial:*" \
"+$site/Spezial:Letzte_Änderungen" \
"-$site/index.php?*" \
"-$site/Diskussion:*" \
"-$site/Benutzer_*" \
"-$site/Kategorie_Diskussion_*" \
"+*.css" 

for page in $(grep "link updated: $site/index.php/" $backupdir/hts-log.txt | sed "s,^.*link updated: $site/index.php/,," | sed ’s/ ->.*//’ | grep -v Spezial:)
do
wget -nv -O $backupdir/$site/index.php/${page}_raw.txt "$topurl/index.php?index=$page&action=raw"
done
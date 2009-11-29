#! /bin/sh

# Inspired by blogpost from http://www-public.it-sudparis.eu/~berger_o/weblog/2008/05/30/offline-backup-mediawiki-with-httrack/

# %i		???
# -w		mirror web sites (--mirror)
# -O 		backup directory
# -%P 		extended parsing, attempt to parse all links, even in unknown tags or Javascript (%P0 don't use) (--extended-parsing[=N])
# -N0 		Saves files like in site Site-structure (default)
# -s0 		follow robots.txt and meta robots tags (0=never,1=sometimes,* 2=always) (--robots[=N])
# -p7 		Expert options, priority mode: 7 > get html files before, then treat other files
# -S 		Expert option, stay on the same directory
# -a 		Expert option, stay on the same address
# -K0 		keep original links (e.g. http://www.adr/link) (K0 *relative link, K absolute links, K3 absolute URI links) (--keep-links[=N]
# -%k 		???
# -A25000 	maximum transfer rate in bytes/seconds (1000=1kb/s max) (--max-rate[=N])
# -F 		user-agent field (-F "user-agent name") (--user-agent )
# -%s		update hacks: various hacks to limit re-transfers when updating (identical size, bogus response..) (--updatehack)
# -x 		Build option, replace external html links by error pages
# -%x 		Build option, do not include any password for external password protected websites (%x0 include) (--no-passwords)
# -%u		???

site=wiki.host.tld
topurl=http://$site

backupdir=~/Downloads/mirrors/$site

httrack -%i -w $topurl/index.php/Special:Allpages \
-O "$backupdir" -%P -N0 -s0 -p7 -S -a -K0 -%k -A25000 \
-F "Mozilla/4.5 (compatible; HTTrack 3.0x; Windows 98)" \
-%s -x -%x -%u \
"-$site/index.php/Special:*" \
"-$site/index.php?title=Special:*" \
"+$site/index.php/Special:RecentChanges" \
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
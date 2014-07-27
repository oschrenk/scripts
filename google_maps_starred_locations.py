# -*- coding: utf-8 -*-
"""
Taken from: https://gist.github.com/endolith/389694

Dependencies:

    pip install lxml
    pip install simplekml

Usage:

    Go to Google Bookmarks: https://www.google.com/bookmarks/

    On the bottom left, click "Export bookmarks": https://www.google.com/bookmarks/bookmarks.html?hl=en

    After downloading the html file, run this script on it to generate a Kml.

"""

from lxml.html import document_fromstring
import simplekml

from urllib2 import urlopen
import re
import time

filename = r'GoogleBookmarks.html'

with open(filename) as bookmarks_file:
    data = bookmarks_file.read()

kml = simplekml.Kml()

# Hacky and doesn't work for all of the stars:
lat_re = re.compile('markers:[^\]]*latlng[^}]*lat:([^,]*)')
lon_re = re.compile('markers:[^\]]*latlng[^}]*lng:([^}]*)')
coords_in_url = re.compile('\?q=(-?\d{,3}\.\d*),\s*(-?\d{,3}\.\d*)')

doc = document_fromstring(data)
for element, attribute, url, pos in doc.body.iterlinks():
    if 'maps.google' in url:
        description = element.text or ''
        print description.encode('UTF8')
        print u"URL: {0}".format(url)

        if coords_in_url.search(url):
            # Coordinates are in URL itself
            latitude = coords_in_url.search(url).groups()[0]
            longitude = coords_in_url.search(url).groups()[1]
        else:
            # Load map and find coordinates in source of page
            try:
                sock = urlopen(url.replace(' ','+').encode('UTF8'))
            except Exception, e:
                print 'Connection problem:'
                print repr(e)
                print 'Waiting 2 minutes and trying again'
                time.sleep(120)
                sock = urlopen(url.replace(' ','+').encode('UTF8'))
            content = sock.read()
            sock.close()
            time.sleep(3) # Don't annoy server
            try:
                latitude = lat_re.findall(content)[0]
                longitude = lon_re.findall(content)[0]
            except IndexError:
                print '[Coordinates not found]'
                print
                continue

        print latitude, longitude
        try:
            kml.newpoint(name=description,
                         coords=[(float(longitude), float(latitude))])
        except ValueError:
            print '[Invalid coordinates]'
        print

kml.save("GoogleBookmarks.kml")

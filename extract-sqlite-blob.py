#!/usr/bin/python

import sqlite3
conn = sqlite3.connect('sp_radio_0.localstorage')
cursor = conn.cursor()

with open("output.json", "wb") as output_file:
    cursor.execute("SELECT value FROM ItemTable where key='RecentStations';")
    ablob = cursor.fetchone()
    output_file.write(ablob[0])

cursor.close()
conn.close()
#!/usr/bin/python

import sqlite3
conn = sqlite3.connect('sp_radio_0.localstorage')
cursor = conn.cursor()

with open("output.json", "rb") as input_file:
    ablob = input_file.read()
    cursor.execute("UPDATE ItemTable SET value=? WHERE key='RecentStations'; ", [sqlite3.Binary(ablob)])
    conn.commit()

cursor.close()
conn.close()
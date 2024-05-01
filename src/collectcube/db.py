#!/usr/bin/env python
# coding: utf-8

import os
import sys
import sqlite3

def make_db():
    connection = sqlite3.connect('landcover.db')
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS PixelVerification (recID INT, PID TEXT, imgDate TEXT, LC5 TEXT, LC25 TEXT)''')
    connection.commit()
    connection.close()
make_db()
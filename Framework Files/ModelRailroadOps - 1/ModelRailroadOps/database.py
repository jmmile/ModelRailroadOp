import sqlite3,os
from config import DB_FILE
def initialize_database():
 os.makedirs('data',exist_ok=True)
 con=sqlite3.connect(DB_FILE);c=con.cursor()
 c.execute('CREATE TABLE IF NOT EXISTS cars(id INTEGER PRIMARY KEY, reporting_mark TEXT, number TEXT)')
 c.execute('CREATE TABLE IF NOT EXISTS industries(id INTEGER PRIMARY KEY, name TEXT)')
 con.commit();con.close()

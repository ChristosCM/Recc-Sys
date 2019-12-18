import sqlite3
import os 
from functions.sqlfunc import sqlQuery

conn = sqlite3.connect('./database/TestDB.db')  # You can create a new database by changing the name within the quotes
#c = conn.cursor() # The database will be saved in the location where your 'py' file is saved

def create(conn):
    if os.path.exists('./database/TestDB.db'): #remove database if it already exists so we can create it again
        os.remove('./database/TestDB.db')
    conn = sqlite3.connect('./database/TestDB.db')
    # Create table - CLIENTS
    conn.execute('''CREATE TABLE ratings
                ([generated_id] INTEGER PRIMARY KEY,[UserID] integer, [BookID] integer, [Rating] float)''');
            
    # Create table - COUNTRY
    conn.execute('''CREATE TABLE books
                ([generated_id] INTEGER PRIMARY KEY,[BookID] integer, [BookTitle] text,[Genres] text);''')
    conn.execute('''CREATE TABLE users(
        userid integer PRIMARY KEY,
        name text NOT NULL,
        pass text
    );
    ''')
    return conn
def addData(conn):
    conn.execute('''INSERT INTO ratings
    VALUES (0,1,1,3.5)
    ''')
print (sqlQuery('''SELECT * FROM ratings'''))
#create(conn)
#addData(conn)                   
conn.commit()

# Note that the syntax to create new tables should only be used once in the code (unless you dropped the table/s at the end of the code). 
# The [generated_id] column is used to set an auto-increment ID for each record
# When creating a new table, you can add both the field names as well as the field formats (e.g., Text)

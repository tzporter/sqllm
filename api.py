import requests
import sqlite3
from sqlite3 import Error
import pandas as pd
from dotenv import load_dotenv
import os
import json

load_dotenv()


DEVMODE = True
TABLE_NAME = "Bitcoin_History"
DB_NAME = "sql.db"
METADATA = "sqldb.json"

API_URL = "https://api-inference.huggingface.co/models/codellama/CodeLlama-34b-Instruct-hf"
token = os.getenv("HF_TOKEN")
headers = {"Authorization": f"Bearer {token}"}

modify_tokens = [ 'ADD', 'ALTER', 'CREATE', 'REPLACE', 'DELETE', 'DROP', 'EXEC', 'INSERT', 'TRUNCATE', 'UPDATE', ]

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.json()

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn
	
def enter_continue():
    c = input("Press enter to keep querying or Q to quit: ").upper()
    if c == "Q": 
        return True
    
    return False

def get_table_metadata(table_name, db_name, metadata_name):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    table_name = table_name
    cur.execute(f"PRAGMA table_info({table_name})")

    rows = cur.fetchall()

    schema = ""
    with open(metadata_name) as f:
        comment_dict = json.load(f)

        for row in rows:
            schema += f'\t{row[1]} {row[2]}, -- {comment_dict[row[1]]}\n'

    return schema

def get_instruction(TABLE_NAME, DB_NAME, METADATA, prompt):
    return f"""
[INST] Write code to solve the following coding problem that obeys the constraints and passes the example test cases. Please wrap your code answer using ```:
### Task
Generate a SQL query to answer the following question:
`{prompt}`

### Database Schema
This query will run on a database whose schema is represented in this string:
Table Name: {TABLE_NAME}
{get_table_metadata(TABLE_NAME, DB_NAME, METADATA)}

### Examples
The following are examples to help illustrate the desired user response.

Prompt: What are the product names?
SQL: SELECT name FROM products;

Prompt: When did ID=20 make a purchase?
SQL: SELECT salesperson_id, sale_date FROM products WHERE salesperson_id=20;

### SQL
Given the database schema, here is the SQL query that answers `{prompt}`. Do not provide explanation and only provide SQL code.:
[/INST]
```sql
"""



conn = create_connection('sql.db')
while True:
    prompt = input("Database Query: ")

    output = query({
    	"inputs": get_instruction(TABLE_NAME, DB_NAME, METADATA, prompt),
    })

    output_text = str(output[0]['generated_text'])
    sql_input = output_text.split('[/INST]\n```sql')[1].replace('```','')

    if DEVMODE:
        print(sql_input)
        q = input("Does this query look correct? (y/N) ").upper()
        if q == "N" or q == "":
            
            if enter_continue():
                break
            else:
                continue
    else:
        #Filter out commands that might modify the database
        flagged = False
        for keyword in modify_tokens:
          if(keyword in sql_input.upper()):
            print(f'Given command contains an editing word {keyword}. Please try again!')
            flagged = True
            break
          
        if flagged:
            if enter_continue():
                break
            else:
                continue

    df = pd.read_sql_query(sql_input, conn)
    print(df)

    if enter_continue():
        break
conn.close()


"""
#CREATE TABLE Bitcoin_History (
#  Index INTEGER PRIMARY KEY, -- Unique ID for each product
#  Date DATE_FORMAT(), -- Date of the recorded data
#  Price DECIMAL(10,2), -- Closing price of Bitcoin on the given date
#  Open DECIMAL(10,2), -- Opening price of Bitcoin on the given date
#  High DECIMAL(10,2), -- Highest price of Bitcoin on the given date
#  Low DECIMAL(10,2), -- Lowest price of Bitcoin on the given date
#  Change DECIMAL(1,10) -- Percentage change in Bitcoin's price from the previous day. stored as decimal. not percent.
#);
"""
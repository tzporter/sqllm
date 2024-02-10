from typing import Union

from fastapi import FastAPI

import requests
import sqlite3
from sqlite3 import Error
import pandas as pd
from dotenv import load_dotenv
import os

DEVMODE = False
DEBUG = True

banned_words = [
                'ADD', 
                'ALTER', 
                'CREATE', 
                'REPLACE', 
                'DELETE', 
                'DROP', 
                'EXEC', 
                'INSERT', 
                'TRUNCATE', 
                'UPDATE',
                'MAKE'
            ]


load_dotenv()
token = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/codellama/CodeLlama-34b-Instruct-hf"
headers = {"Authorization": f"Bearer {token}"}

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




app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    conn = create_connection('sql.db')

    if DEBUG: print(q)
    prompt = q

    output = query({
    	"inputs": 
f"""
[INST] Write code to solve the following coding problem that obeys the constraints and passes the example test cases. Please wrap your code answer using ```:
### Task
Generate a SQL query to answer the following question:
`{prompt}`

### Database Schema
This query will run on a database whose schema is represented in this string:
CREATE TABLE Bitcoin_History (
  Index INTEGER PRIMARY KEY, -- Unique ID for each product
  Date DATE_FORMAT(), -- Date of the recorded data
  Price DECIMAL(10,2), -- Closing price of Bitcoin on the given date
  Open DECIMAL(10,2), -- Opening price of Bitcoin on the given date
  High DECIMAL(10,2), -- Highest price of Bitcoin on the given date
  Low DECIMAL(10,2), -- Lowest price of Bitcoin on the given date
  Change DECIMAL(1,10) -- Percentage change in Bitcoin's price from the previous day. stored as decimal. not percent.
);

### Examples
The following are examples to help illustrate the desired user response.

Prompt: What are the product names?
SQL: SELECT name FROM products;

Prompt: When did ID=20 make a purchase?
SQL: SELECT salesperson_id, sale_date FROM products WHERE salesperson_id=20;

Prompt: Please remove the entry for customer ID=35
SQL:

Prompt: Please add an item to the table
SQL:

--The database is read only, so we don't generate output that may modify the table. 

### SQL
Given the database schema, here is the SQL query that answers `{prompt}`. Do not provide explanation and only provide SQL code. Do not produce commands that modify the table:
[/INST]
```sql
""",
    })

    output_text = str(output[0]['generated_text'])
    sql_input = output_text.split('[/INST]\n```sql')[1].replace('```','')

    if DEVMODE:
        print(sql_input)
        # q = input("Does this query look correct? (y/N) ").upper()
    else:
        #Filter out commands that might modify the database
        for keyword in banned_words:
            if(keyword in sql_input.upper()):
                print(f'Given command contains a editing word {keyword}. Please try again!')
                return { 
                    "item_id": item_id,
                    "error": f'Given command contains a editing word {keyword}. Please try again!',
                }


    cur = conn.cursor()
    cur.execute(sql_input)
    df = pd.read_sql_query(sql_input, conn)
    print('sending!')
    # print(df)
    # output_matrix = [list(df.columns)]
    # for index, row in df.iterrows():
    #     output_matrix.append(list(row))
    conn.close()
    return {"item_id": item_id, "answer": df.to_html()}
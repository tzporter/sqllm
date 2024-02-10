from typing import Union

from fastapi import FastAPI

import requests
import sqlite3
from sqlite3 import Error
import pandas as pd
from dotenv import load_dotenv
import os
import json

DEVMODE = False
DEBUG = True

DB_NAME = "sql.db"
TABLE_NAME = "Bitcoin_History"
METADATA = "sqldb.json"

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


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/query/{item_id}")
def get_sql_command(item_id: int, prompt: Union[str, None] = None):
    if DEBUG: print(prompt)

    output = query({
    	"inputs": get_instruction(TABLE_NAME, DB_NAME, METADATA, prompt),
    })

    output_text = str(output[0]['generated_text'])
    sql_input = output_text.split('[/INST]\n```sql')[1].replace('```','')

    return sql_input

@app.get("/runsql/{item_id}")
def run_sql_command(item_id: int, sql: Union[str, None] = None):
    conn = create_connection(DB_NAME)

    #cur = conn.cursor()
    
    #cur.execute(sql)
    df = pd.read_sql_query(sql, conn)
    print('sending!')
    output_matrix = [list(df.columns)] + df.values.tolist()
    conn.close()
    return {"item_id": item_id, "answer": output_matrix}




    #Extract to Javascript
    #if DEVMODE:
    #    print(sql_input)
    #    # q = input("Does this query look correct? (y/N) ").upper()
    #else:
    #    #Filter out commands that might modify the database
    #    for keyword in banned_words:
    #        if(keyword in sql_input.upper()):
    #            print(f'Given command contains a editing word {keyword}. Please try again!')
    #            return { 
    #                "item_id": item_id,
    #                "error": f'Given command contains a editing word {keyword}. Please try again!',
    #            }


    
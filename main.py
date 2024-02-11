from typing import Union

# from fastapi import FastAPI
from nicegui import ui
from nicegui.events import KeyEventArguments
# import frontend

import requests
import sqlite3
from sqlite3 import Error
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype
from dotenv import load_dotenv
import os
import json

ui.label('Hello NiceGUI!')

# app = FastAPI()
# frontend.init(app)


# @app.get("/")
# def read_root():
#     return {"Hello": "World"}

# if __name__ == '__main__':
#     print('Please start the app with the "uvicorn" command as shown in the start.sh script')

user_input = ui.input(value='', placeholder='enter prompt')
ouput = ui.label('hello')

def update(*, df: pd.DataFrame, r: int, c: int, value):
    df.iat[r, c] = value
    ui.notify(f'Set ({r}, {c}) to {value}')
grid = ui.grid(rows=10, columns=10)

def handle_key(e: KeyEventArguments):
    print(e.key)
    if e.key == 'Enter':
        if e.action.keydown:
            # (user_input.value)
            sql_command = get_sql_command(user_input.value)
            result_df = run_sql_command(sql_command)
            # result_df = 5
            with ui.grid(rows=len(result_df.index)+1).classes('grid-flow-col'):
                for c, col in enumerate(result_df.columns):
                    ui.label(col).classes('font-bold')
                    for r, row in enumerate(result_df.loc[:, col]):
                        if is_bool_dtype(result_df[col].dtype):
                            cls = ui.checkbox
                        elif is_numeric_dtype(result_df[col].dtype):
                            cls = ui.number
                        else:
                            cls = ui.input
                        cls(value=row, on_change=lambda event, r=r, c=c: update(df=result_df, r=r, c=c, value=event.value))
            # ouput.set_text(result_df.to_string())
keyboard = ui.keyboard(on_key=handle_key)
ui.run()
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




#MAY NEED TO REMOVE NEWLINES AND CHANGE SPACES TO %20 FOR API CALL!
# @app.get("/query/{item_id}")
def get_sql_command(prompt: Union[str, None] = None):
    if DEBUG: print(prompt)

    output = query({
    	"inputs": get_instruction(TABLE_NAME, DB_NAME, METADATA, prompt),
    })

    output_text = str(output[0]['generated_text'])
    sql_input = output_text.split('[/INST]\n```sql')[1].replace('```','')

    return sql_input

# @app.get("/runsql/{item_id}")
def run_sql_command(sql: Union[str, None] = None) -> pd.DataFrame:
    conn = create_connection(DB_NAME)

    # try: 
    df = pd.read_sql_query(sql, conn)
    # output_matrix = [list(df.columns)] + df.values.tolist()
    # except:
    #     print(sql)
    #     output_matrix = "ERROR in main.py. check python console/"
    return df#{"item_id": item_id, "answer": output_matrix}




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


    
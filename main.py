from typing import Union

# from fastapi import FastAPI
from nicegui import ui
from nicegui.events import KeyEventArguments, ValueChangeEventArguments
import requests
import sqlite3
from sqlite3 import Error
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype
from dotenv import load_dotenv
import os
import json

# data object
class Data:
    def __init__(self):
        self.dev_mode = False
        self.generated_sql = ""
        self.clean_sql = ""
        #self.accept_code = False
        self.show_accept_buttons=False

    def clear_sql(self):
        self.generated_sql = ""
        self.clean_sql = ""
data = Data()

# defining dark mode
dark = ui.dark_mode()
def toggle_dark():
    if data.dev_mode:
        dark.enable()
        ui.notify('Developer Mode: Enabled')
    else:
        dark.disable()
        ui.notify('Developer Mode Disabled')
        data.clear_sql()

        data.show_accept_buttons = False
    table_manager.grid.clear()


# table constructor
class table_manager:
    @staticmethod
    def update_table(dataframe):
        table_manager.grid.delete()
        print(dataframe.columns)
        table_manager.grid = ui.grid(rows=len(dataframe.index)+1)
        with table_manager.grid.classes('grid-flow-col'):
            for c, col in enumerate(dataframe.columns):
                ui.label(col).classes('font-bold')
                for r, row in enumerate(dataframe.loc[:, col]):
                    if is_bool_dtype(dataframe[col].dtype):
                        cls = ui.label
                    elif is_numeric_dtype(dataframe[col].dtype):
                        cls = ui.label
                    else:
                        cls = ui.label
                    cls(row)
                for num in range(10-len(dataframe.columns)):
                    ui.label('*')


# defining enter behavior
def enter_callback():
    result_df = process_query(user_input_textbox.value)
    if result_df is None:
        return
    # print(result_df)
    table_manager.update_table(result_df)

    #ui.notify(f'{name}: {event.value}')

def approve_code_callback(accept_bool):
    if accept_bool:
        print(data.clean_sql)
        table_manager.update_table(run_sql_command(data.clean_sql))

        #data.accept_code = False
        data.show_accept_buttons = False    
    else:
        data.clear_sql()
    
        data.show_accept_buttons = False

#initializing layout
default_style = '''
  font-family: Roboto Mono, monospace;
'''

ui.label.default_style(default_style)
ui.input.default_style(default_style)
ui.button.default_style(default_style)

with ui.row().classes('items-center').classes('w-full justify-between'):
    dummy = ui.label('')
    title = ui.label('Welcome to SQLLM!')
    switch = ui.switch('', 
                       on_change=toggle_dark).bind_value(data, 'dev_mode')
with ui.card().props("size=100").style('margin: auto'):

    with ui.column():
        with ui.row().classes('items-center'):
            label = ui.label('Query:')
            user_input_textbox = ui.input(placeholder='Example: What is the highest price achieved').on('keydown.enter', enter_callback).props("size=60")

        dev_code_textbox = ui.markdown('').bind_content_from(data, 'generated_sql').bind_visibility(data, 'dev_mode')
        with ui.row():
            ui.button('Approve', on_click=lambda: approve_code_callback(True), ).bind_visibility(data, 'show_accept_buttons')
            ui.button('Reject', on_click=lambda: approve_code_callback(False), ).bind_visibility(data, 'show_accept_buttons')


table_manager.grid = ui.grid(columns=2)

#keyboard = ui.keyboard(on_key=handle_key)
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



ui.run()

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

def process_query(prompt):
    sql = get_sql_command(prompt)

    if data.dev_mode:
       data.clean_sql = sql
       data.generated_sql = f"Generated SQL query:\n```sql\n{sql}\n```"
       data.show_accept_buttons=True
       table_manager.grid.clear()

       return None
       #print(sql)
       # q = input("Does this query look correct? (y/N) ").upper()
    else:
       #Filter out commands that might modify the database
        for keyword in banned_words:
           if(keyword in sql.upper()):
                #data.generated_sql = f'Given command contains an editing word {keyword}. Please try again!'
                ui.notify('Generated SQL contained unsafe commands. Please Try Again!', type='warning')
                return
    
        return run_sql_command(sql)
    

#MAY NEED TO REMOVE NEWLINES AND CHANGE SPACES TO %20 FOR API CALL!
def get_sql_command(prompt: Union[str, None] = None):
    if DEBUG: print(prompt)

    output = query({
    	"inputs": get_instruction(TABLE_NAME, DB_NAME, METADATA, prompt),
    })
    try:
        output_text = str(output[0]['generated_text'])
        sql_input = output_text.split('[/INST]\n```sql')[1].replace('```','')
    except:
        raise Exception(output)

    return sql_input

def run_sql_command(sql: Union[str, None] = None) -> pd.DataFrame:
    conn = create_connection(DB_NAME)

    try: 
        df = pd.read_sql_query(sql, conn)
    except:
        ui.notify('SQL isn\'t runnable. please try again!', type='warning')
        df = pd.DataFrame()
    return df#{"item_id": item_id, "answer": output_matrix}


    
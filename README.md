# SQLLM

SQLLM was made for the Hacklytics competition at Georgia Tech. It takes a user request and uses CodeLlama to generate the proper SQL command to answer the user request based on the available table. Normal mode is for non-technical users, which does not display the SQL command and only allows read only commands. Developer mode is for advanced users, showing the SQL query before it is run for developer approval and allowing modification to the database. We use NiceGUI for the front end.

## Setup
Run
```sh
git clone https://github.com/tzporter/sqllm
pip install -r requirements.txt
```
to clone the repo and install the required python packages.
Next, configure the .env file to set `HF_TOKEN` with your personal HuggingFace token. Finally, edit `DB_NAME`, `TABLE_NAME` and `METADATA` in `main.py` with your personal database and table. Metadata is a file like the included `sqldb.json`, which includes a short description for every column header to provide context for CodeLlama

## Run
Simply run 
```sh
python3 main.py
```
and NiceGUI will open on your localhost. 

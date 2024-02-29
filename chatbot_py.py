from flask import Flask, request, render_template, jsonify
import openai
import re
import requests
import json
import sqlite3
import pandas as pd
import tkinter as tk
from tkinter import filedialog

app = Flask(__name__)

db_name = "mydatabase.db"

def combo():
    # 1. Connect to the SQLite database
    conn = sqlite3.connect(db_name)
    # 2. Create a cursor object to execute SQL queries
    cursor = conn.cursor()
    # 3. Query the SQLite database to fetch all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    # 4. Fetch the table names
    table_names = cursor.fetchall()
    table_col_combo = []
    # 5. Iterate through the table names and fetch their column names
    for table_name in table_names:
        table_name = table_name[0]  # Extract the table name from the result

        # Query to fetch column names of the current table
        query = f"PRAGMA table_info({table_name});"
        cursor.execute(query)

        # Fetch the column names for the current table
        column_names = [row[1] for row in cursor.fetchall()]

        # Print or use the table name and column names
        print("Table:", table_name)
        print("Columns:", column_names)
        combo = f"'{table_name}' has columns {column_names}"
        print(combo)
        table_col_combo.append(combo)
        
    print(table_col_combo)
    # 6. Close the cursor and the database connection
    cursor.close()
    conn.close()
    return table_col_combo


# Set your OpenAI API key
openai.api_key = "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"

messages = [
    {"role": "system", "content": "You are a helpful and kind AI Assistant."},
]

def chatbot(input):
    if input:
        table_col_combo = combo()
        print(f"Write an SQLite command to {input} if the table and their columns are {table_col_combo}")
        messages.append({"role": "user", "content": f"Write an SQLite command for {input}.Pre exisiting tables and their columns are {table_col_combo}"})
        chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        reply = chat.choices[0].message.content
        print(reply)
        messages.append({"role": "assistant", "content": reply})
        extracted_content = re.findall(r"```sqlite(.*?)```", reply, re.DOTALL) or re.findall(r"```sql(.*?)```", reply, re.DOTALL) or re.findall(r"```(.*?)```", reply, re.DOTALL) 
        responses = []
        print(extracted_content)
        for content in extracted_content:
            reply = content.strip()
            print(reply)
            url = 'http://localhost:5000/execute'
            data = {'sql_command': reply}
            headers = {'Content-Type': 'application/json'}
    
            response = requests.post(url, data=json.dumps(data), headers=headers)
            if response.status_code == 200:
                print('Request successful')
            else:
                print('Request failed:', response.text)
            responses.append(response.json())            
        return responses



#Routes for Website
@app.route("/")
def index():
    return render_template('index.html')


@app.route("/get", methods=["GET", "POST"])
def chat():
    input = request.form["msg"]
    print("Input: " + input)
    responses = chatbot(input)
    print(responses)
    print(type(responses))
    return responses

@app.route('/add', methods=['POST'])
def browse_file():
    root = tk.Tk()   # Create a file dialog window 
    root.withdraw()  # Hide the main window

    # Open a file dialog and get the selected file's path
    file_path = filedialog.askopenfilename(
        initialdir="/",  # Set the initial directory (change this to your preferred directory)
        title="Select Table File in CSV Format",  # Set the title of the dialog box
        filetypes=(("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")),  # Specify allowed file types
        initialfile="",  # Set the initial file (blank for none)
        parent=root,  # Set the parent window
        multiple=False,  # Allow multiple file selection
        defaultextension=".csv",  # Set a default extension for files
    )

    # Ensure a file was selected before proceeding
    if file_path:
        print(f"Selected File: {file_path}")
        # Use the split method to separate the path into parts using the '/' character
        path_parts = file_path.split('/')
        # Extract the last part, which is the filename, and split it using '.' to get the base filename
        filename = path_parts[-1]
        base_filename = filename.split('.')[0]
        print(base_filename)
        df =  pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        connection = sqlite3.connect(db_name)
        df.to_sql(base_filename, connection, if_exists = 'replace')
        connection.close()


@app.route('/show', methods=['POST'])
def show_file():

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    
    # Fetch data from each table
    data = {}
    for table in tables:
        query = f"PRAGMA table_info({table});"
        cursor.execute(query)

        # Fetch the column names for the current table
        column_names = [row[1] for row in cursor.fetchall()]
        tuple_of_col = tuple(column_names)
        cursor.execute(f"SELECT * FROM {table};")
        table_data = cursor.fetchall()
        table_data.insert(0, tuple_of_col)
        table_data = [list(t) for t in table_data]
        data[table] = table_data
    conn.close()
    print(data)
    print(type(data))
    return jsonify({'output_value': data})


if __name__ == '__main__':
    app.run(debug=True,port = 5002)
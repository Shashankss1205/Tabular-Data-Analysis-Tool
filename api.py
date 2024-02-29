from flask import Flask, request, jsonify
import sqlite3
from chatbot_py import db_name

app = Flask(__name__)

# Function to establish a database connection
def get_db_connection():
    conn = sqlite3.connect(db_name)
    return conn

# API route to execute SQL commands
@app.route('/execute', methods=['POST'])
def execute_sql():
    try:
        data = request.get_json()
        sql_command = data.get('sql_command')

        if not sql_command:
            return jsonify({'error': 'SQL command is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        # Split the SQL script into individual SQL commands
        sql_commands = [command.strip() for command in sql_command.split(';') if command.strip()]

        # Print the list of SQL commands
        for sql_command in sql_commands:
            print(sql_command)
            # Check if the SQL command is a SELECT statement
            is_select_query = sql_command.strip().upper().startswith('SELECT')
            cursor.execute(sql_command)
            # # If it's a SELECT statement, fetch and return the query result
            if is_select_query:
                tables = cursor.fetchall()
                print(tables)
                conn.commit()

            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = f"Tables Available: {cursor.fetchall()}"
                conn.commit()
        print(tables)
        return tables

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
import sqlite3
import json


def create_database(db_path='q_table.db'):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Drop the table if it already exists to avoid schema conflicts
    cur.execute('DROP TABLE IF EXISTS QTable')
    # Create the table with the correct columns
    cur.execute('''
    CREATE TABLE QTable (
        state TEXT,
        action TEXT,
        value REAL,
        PRIMARY KEY (state, action)
    )
    ''')
    conn.commit()
    conn.close()


def import_json_to_db(json_path, db_path='q_table.db'):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    with open(json_path, 'r') as file:
        data = json.load(file)
        for state, actions in data.items():
            for action, value in actions.items():
                cur.execute('INSERT OR IGNORE INTO QTable (state, action, value) VALUES (?, ?, ?)',
                            (state, action, value))
    conn.commit()
    conn.close()


create_database()  # Create the database and table
import_json_to_db('decision.json')  # Import JSON data to the SQLite database

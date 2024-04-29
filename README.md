# SkullKingAI
__game.py__ is used for a player to play a game against trained models. A q_table.db file is required for this.<br />
__evaluate_sql.py__ is a script to measure performance metrics for the trained AI model over many simulated games, and produce visualizations of the data.<br />
__evaluate_json.py__ is a similar script that reads from the previous method of storing the q_table as a json<br />
__training.py__ trains the model and saves to a json format<br />
__training_sql.py__ trains the model, reading from a sql data base. This is a work in progress and needs to be modified in order to properly handle read/write conflicts in the database.<br />
__combine_tables.py__ combines the q_tables produced from the training.py script and combines them into a single json file.<br />
__json_sqlite.py__ converts json format q_tables into a sql data base which is useable by evaluate_sql.py and game.py<br />
__main.py__ is a remnant from previous versions and is currently not functional<br />

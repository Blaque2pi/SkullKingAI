# SkullKingAI
game.py is used for a player to play a game against trained models. A q_table.db file is required for this./n
evaluate_sql.py is a script to measure performance metrics for the trained AI model over many simulated games, and produce visualizations of the data./n
evaluate_json.py is a similar script that reads from the previous method of storing the q_table as a json/n
training.py trains the model and saves to a json format/n
training_sql.py trains the model, reading from a sql data base. This is a work in progress and needs to be modified in order to properly handle read/write conflicts in the database./n
combine_tables.py combines the q_tables produced from the training.py script and combines them into a single json file./n
json_sqlite.py converts json format q_tables into a sql data base which is useable by evaluate_sql.py and game.py/n
main.py is a remnant from previous versions/n

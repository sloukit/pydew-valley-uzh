import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path='data/database/database.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY,
                npc_name TEXT,
                interaction_time TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS map_switches (
                id INTEGER PRIMARY KEY,
                from_map TEXT,
                to_map TEXT,
                switch_time TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS goggles_wearing (
                id INTEGER PRIMARY KEY,
                worn BOOLEAN,
                wear_time TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bath_house_entries (
                id INTEGER PRIMARY KEY,
                health_state TEXT,
                health INTEGER,
                entry_time TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_switches (
                id INTEGER PRIMARY KEY,
                old_group INTEGER,
                new_group INTEGER,
                switch_time TIMESTAMP
            )
        ''')
        self.conn.commit()

    def log_interaction(self, npc_name):
        self.cursor.execute('''
            INSERT INTO interactions (npc_name, interaction_time)
            VALUES (?, ?)
        ''', (npc_name, datetime.now()))
        self.conn.commit()

    def log_map_switch(self, from_map, to_map):
        self.cursor.execute('''
            INSERT INTO map_switches (from_map, to_map, switch_time)
            VALUES (?, ?, ?)
        ''', (from_map, to_map, datetime.now()))
        self.conn.commit()

    def log_goggles_wearing(self, worn):
        self.cursor.execute('''
            INSERT INTO goggles_wearing (worn, wear_time)
            VALUES (?, ?)
        ''', (worn, datetime.now()))
        self.conn.commit()

    def log_bath_house_entry(self, health_state, health):
        self.cursor.execute('''
            INSERT INTO bath_house_entries (health_state, health, entry_time)
            VALUES (?, ?, ?)
        ''', (health_state, health, datetime.now()))
        self.conn.commit()

    def log_group_switch(self, old_group, new_group):
        self.cursor.execute('''
            INSERT INTO group_switches (old_group, new_group, switch_time)
            VALUES (?, ?, ?)
        ''', (old_group, new_group, datetime.now()))
        self.conn.commit()

    def close(self):
        self.conn.close()


# Example usage:

# Log an interaction with an NPC
# db.log_interaction("John the NPC")

# Log a map switch
# db.log_map_switch("Map1", "Map2")

# Log the player wearing goggles
# db.log_goggles_wearing(True)

# Log a bath house entry
# db.log_bath_house_entry("Healthy, 90)

# Log a group switch
# db.log_group_switch(1, 2)
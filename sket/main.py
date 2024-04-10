import sqlite3
connection = sqlite3.connect('Base.db')
cursor = connection.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS Users
              (user_id INTEGER PRIMARY KEY AUTOINCREMENT, user_name TEXT, user_password TEXT, salt TEXT)''')
connection.commit()
cursor.execute('''CREATE TABLE IF NOT EXISTS groups
              (group_id INTEGER PRIMARY KEY AUTOINCREMENT, group_name TEXT)''')
connection.commit()
cursor.execute('''CREATE TABLE IF NOT EXISTS files
              (uuid TEXT PRIMARY KEY, virtual_path TEXT, created_at TEXT, owner_user_id INT, owner_group_id INT, mode INT, file_name TEXT,FOREIGN KEY(owner_user_id) REFERENCES users(user_id),FOREIGN KEY(owner_group_id) REFERENCES groups(group_id))''')
connection.commit()
cursor.execute('''CREATE TABLE IF NOT EXISTS connections
              (user_id INTEGER, group_id INTEGER, FOREIGN KEY(group_id) REFERENCES groups(group_id),FOREIGN KEY(user_id) REFERENCES users(user_id))''')
connection.commit()
connection.close()
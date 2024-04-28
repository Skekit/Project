import sqlite3
connection = sqlite3.connect('Base.db')
cursor = connection.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS Users
              (id  INTEGER UNIQUE PRIMARY KEY AUTOINCREMENT, name  TEXT UNIQUE, password TEXT, salt TEXT)''')
connection.commit()
cursor.execute('''CREATE TABLE IF NOT EXISTS groups
              (id INTEGER UNIQUE PRIMARY KEY AUTOINCREMENT, name  TEXT UNIQUE)''')
connection.commit()
cursor.execute('''CREATE TABLE IF NOT EXISTS files
              (id INTEGER UNIQUE PRIMARY KEY AUTOINCREMENT, virtual_path TEXT, created_at TEXT, owner_user_id INT, owner_group_id INT, mode INT, name  TEXT UNIQUE,FOREIGN KEY(owner_user_id) REFERENCES users(user_id),FOREIGN KEY(owner_group_id) REFERENCES groups(group_id))''')
connection.commit()
cursor.execute('''CREATE TABLE IF NOT EXISTS connections
              (user_id INTEGER, group_id INTEGER, FOREIGN KEY(group_id) REFERENCES groups(group_id),FOREIGN KEY(user_id) REFERENCES users(user_id))''')
connection.commit()
connection.close()
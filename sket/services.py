import os
import sqlite3
import argon2
import datetime
import hashlib
from fastapi import  Depends
from models import User, File, Group

ph = argon2.PasswordHasher()

def get_db():
    connection = sqlite3.connect('Base.db')
    connection.row_factory = sqlite3.Row
    try:
        yield connection.cursor()
    finally:
        connection.commit()
        connection.close()

    

def salt_and_hash_password(password):
    salt = os.urandom(16)
    salted_password = salt + password.encode('utf-8')
    hashed_password = ph.hash(salted_password)
    #hashed_password = hashlib.sha256(salted_password).hexdigest()
    return salt, hashed_password

def password_correct(hash,salt,password):
    salted_password = salt + password.encode('utf-8')
    #hashed_password = ph.hash(salted_password)
    #hashed_password = hashlib.sha256(salted_password).hexdigest()
    #if hashed_password==hash:
    #    return True
    #else:
    #    return False
    try:
        ph.verify(hash,salted_password)
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False



def new_file(user_name,mode,file_name, cursor: sqlite3.Cursor):
        dt_now = str(datetime.datetime.now())
        cursor.execute("""SELECT * FROM Users WHERE name = ?""", ((user_name,)))
        fetched_user = User(**cursor.fetchone())
        virtual_path = f"files/{user_name}/{file_name}"
        group_id=Group.getByUserName(user_name,cursor)
        cursor.execute('''INSERT INTO files( virtual_path, created_at, owner_user_id, owner_group_id, mode, name)
                       VALUES( ?, ?, ?, ?, ?, ?)''', ( virtual_path, dt_now, fetched_user.id, group_id.id, mode, file_name))
        
        

def Create_user(name,password, cursor: sqlite3.Cursor):
    salt,hashed_password=salt_and_hash_password(password)
    cursor.execute('''INSERT INTO Users( name, password, salt)
            VALUES( ?, ?, ?)''', ( name, hashed_password, salt))

def Have_access_2(mode, owner_user_id, username, user_id, owner_group_id,cursor: sqlite3.Cursor):
    if owner_user_id==user_id:
        if mode//100>1:
            return True
        else:
            return False
    else:
        if mode//10%10>1:
            group_id=Group.getByUserName(username,cursor)
            if group_id==owner_group_id:
                return True
            else:
                if mode%10>1:
                    return True
                else:
                    return False
        else:
                return False

def Have_access_1(mode, owner_user_id, username, user_id, owner_group_id,cursor: sqlite3.Cursor):
    if owner_user_id==user_id:
        if mode//100>0:
            return True
        else:
            return False
    else:
        if mode//10%10>0:
            group_id=Group.getByUserName(username,cursor)
            if group_id==owner_group_id:
                return True
            else:
                if mode%10>0:
                    return True
                else:
                    return False
        else:
                return False

def delete_file_by_name(filename, cursor: sqlite3.Cursor ):
    cursor.execute("""DELETE FROM files WHERE name = ?""", ((filename,)))

def group_by_name(name, cursor: sqlite3.Cursor):
    return Group.getByName(name,cursor)

def Create_connection(user_name,group_name, cursor: sqlite3.Cursor ):
    try:
        fetched_user=User.getByName(cursor,user_name)
        group = Group.getByName(group_name,cursor)
        if group is None:
            return False
        else:
            cursor.execute('''INSERT INTO connections(group_id , user_id )
                        VALUES(?, ?)''', (group.id,fetched_user.id))
            return True
    except sqlite3.Error as e:
        return False

def Create_group(name, cursor: sqlite3.Cursor ):
    try:
        cursor.execute("SELECT * FROM groups WHERE name = ?",(name))
        if cursor.fetchone() is None:
            cursor.execute('''INSERT INTO groups( name)
                            VALUES(?)''',( name))
            return True
        else:
            return False
    except sqlite3.Error as e:
        return False

def delete_connection(group_name,user_id,cursor: sqlite3.Cursor):
    try:
        group = Group.getByName(group_name,cursor)
        cursor.execute('''DELETE FROM connections WHERE group_id = ? AND user_id = ? ''', (group.id,user_id))
        return True
    except TypeError as e:
        return False

def get_files_names(cursor: sqlite3.Cursor):
    try:
        names=[]
        cursor.execute("SELECT * FROM files")
        files=cursor.fetchall()
        for file in files:
            file=File(**file)
            names.append(file.name)
        return names
    except TypeError as e:
        return f"error {e}"
    
def get_files_names_by_user(name,cursor: sqlite3.Cursor):
    try:
        user=User.getByName(cursor,name)
        names=[]
        cursor.execute("SELECT * FROM files WHERE owner_user_id = ?",(user.id,))
        files=cursor.fetchall()
        for file in files:
            file=File(**file)
            names.append(file.name)
        return names
    except TypeError as e:
        return f"error {e}"


from typing import Optional
from pydantic import BaseModel
import sqlite3



class FeaturedModel(BaseModel):
    class Config: orm_mode = True

class File(FeaturedModel):
    id:int
    virtual_path:str
    created_at:str
    owner_user_id:int
    mode:int
    name:str
    owner_group_id:int=-1
    @staticmethod
    def getByName(filename, cursor: sqlite3.Cursor):
        try:
            cursor.execute("""SELECT * FROM files WHERE name = ?""", ((filename,)))
            return File(**cursor.fetchone())
        except TypeError as e:
            return None

class User(FeaturedModel):
    id:int
    name:str
    password:str
    salt:bytes
    @staticmethod
    def getByName(cursor: sqlite3.Cursor, username: str):
        try:
            cursor.execute("""SELECT * FROM Users WHERE name = ?""", ((username,)))
            return User(**cursor.fetchone())
        except TypeError as e:
            return None
    @staticmethod
    def getById(id,cursor: sqlite3.Cursor):
        try:
            cursor.execute("""SELECT * FROM Users WHERE id = ?""", ((id,)))
            return User(**cursor.fetchone())
        except TypeError as e:
            return None

class New_Connections(FeaturedModel):
    user_name:str
    group_name:str
    user_password:str

class New_user(FeaturedModel):
    name:str
    password:str

class New_group(FeaturedModel):
    group_name:str

class File_param(FeaturedModel):
    user:str
    mode:int

class Get_file(FeaturedModel):
    user_name:str
    password:str
    file_name:str

class Group(FeaturedModel):
    id:int
    name:str
    @staticmethod
    def getByUserName(user_name, cursor: sqlite3.Cursor) -> Optional["Group"]:
        cursor.execute("""
            select g.*
            from Users u
            join connections c on c.user_id = u.id
            join groups g on g.id = c.group_id
            where u.name = ?;
        """, (user_name,))
        res = cursor.fetchone()
        if res is None:
            return None
        #cursor.execute("""SELECT * FROM Users WHERE name =?""", (user_name,))
        #user=User(**cursor.fetchone())
        #cursor.execute("""SELECT * FROM Connections WHERE user_id =?""", (user.id,))
        #group_id=cursor.fetchone()
        #cursor.execute("""SELECT * FROM groups WHERE id =?""", (group_id[0],))
        group=Group(**res)
        return group
        
    @staticmethod
    def getByName(name, cursor: sqlite3.Cursor):
        try:
            cursor.execute("""SELECT * FROM groups WHERE name = ?""", ((name,)))
            return Group(**cursor.fetchone())
        except TypeError as e:
            return None

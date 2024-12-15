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
    def getByName(cursor: sqlite3.Cursor,username: str):
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
    group_name:str
    

class New_user(FeaturedModel):
    name:str
    password:str

class New_group(FeaturedModel):
    group_name:str

class File_param(FeaturedModel):
    user:str
    mode:int

class Get_file(FeaturedModel):
    file_name:str

class Group(FeaturedModel):
    id:int
    name:str
    @staticmethod
    def getByUserName(user_name, cursor: sqlite3.Cursor):
        cursor.execute("""SELECT * FROM Users WHERE name =?""", (user_name,))
        user=User(**cursor.fetchone())
        cursor.execute("""SELECT * FROM Connections WHERE user_id =?""", (user.id,))
        groups=cursor.fetchall()
        list_of_groups=[]
        for i in groups:
            cursor.execute("""SELECT * FROM groups WHERE id =?""", (i[1],))
            #group=Group(**cursor.fetchone())
            temp = cursor.fetchone()
            list_of_groups.append(Group(**temp))
        if list_of_groups != None:
            return(list_of_groups)
        else:
            return(None)
    @staticmethod
    def getByName(name, cursor: sqlite3.Cursor):
        try:
            cursor.execute("""SELECT * FROM groups WHERE name = ?""", ((name,)))
            return Group(**cursor.fetchone())
        except TypeError as e:
            return None
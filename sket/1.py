import os
import sqlite3
import argon2
from argon2 import PasswordHasher
import datetime
import hashlib
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, Form
from starlette.responses import FileResponse
app = FastAPI()

ph = argon2.PasswordHasher()
class file(BaseModel):
    uuid:int
    virtual_path:str
    created_at:str
    owner_user_id:int
    owner_group_id:int=-1
    mode:int
    file_name:str

class user(BaseModel):
    user_id:int
    user_name:str
    user_password:str
    salt:bytes

class new_Connections(BaseModel):
    user_name:str
    group_name:str
    user_password:str

class new_user(BaseModel):
    user_name:str
    password:str

class new_group(BaseModel):
    group_name:str

class file_param(BaseModel):
    user:str
    mode:int
    class Config:
        orm_mode = True

class get_file(BaseModel):
    user_name:str
    password:str
    file_name:str
connection = sqlite3.connect('Base.db')
cursor = connection.cursor()

def group_by_user(user_name):
    
        cursor.execute("""SELECT * FROM Users WHERE user_name =?""", (user_name,))
        user=cursor.fetchone()
        cursor.execute("""SELECT * FROM Connections WHERE user_id =?""", (user[0],))
        group=cursor.fetchone()
        if group!=None:
            return(group[1])
        else:
            return(-1)
    

def salt_and_hash_password(password):
    salt = os.urandom(16)
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    return salt, hashed_password

def password_correct(hash,salt,password):
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    if hashed_password==hash:
        return True
    else:
        return False

def is_permitted(file_name,user_name):
    try:
        connection = sqlite3.connect('Base.db')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM files WHERE uuid =?""", (file_name,))
        fetched_file=file(**cursor.fetchone())
        cursor.execute("""SELECT * FROM Users WHERE user_name =?""", (user_name,))
        fetched_user=user(**cursor.fetchone())
        if fetched_file.owner_user_id==fetched_user.user_id:
            if fetched_file.mode//100>0:
                return True
            else:
                return False
        else:
            try:
                group_id=group_by_user(user_name)
                if group_id==fetched_file.owner_group_id:
                    return True
                else:
                    return False
            except error:
                return False
    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)

def new_file(user_name,mode,file_name):
        print(user_name,mode,file_name)
        connection = sqlite3.connect('Base.db')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        dt_now = str(datetime.datetime.now())
        cursor.execute("""SELECT * FROM Users WHERE user_name = ?""", ((user_name,)))
        fetched_user = user(**cursor.fetchone())
        virtual_path = f"files/{user_name}/{file_name}"
        group_id=group_by_user(user_name)
        cursor.execute("SELECT * FROM files")
        results = cursor.fetchall()
        number = len(results)
        cursor.execute('''INSERT INTO files(uuid, virtual_path, created_at, owner_user_id, owner_group_id, mode, file_name)
                       VALUES(?, ?, ?, ?, ?, ?, ?)''', (number, virtual_path, dt_now, fetched_user.user_id, group_id, mode, file_name))
        print(number, virtual_path, dt_now, fetched_user.user_id, group_id, mode, file_name)
        connection.commit()
        connection.close()

    




@app.post("/upload_file")
async def create_upload_file(thisfile: UploadFile,username: str = Form(), mode: int = Form(),user_password:str=Form()):
    connection = sqlite3.connect('Base.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""SELECT * FROM files WHERE file_name = ?""", ((thisfile.filename,)))
    
    if cursor.fetchone() == None:
        cursor.execute("""SELECT * FROM Users WHERE user_name = ?""", ((username,)))
        fetched_user = user(**cursor.fetchone())
        if password_correct(fetched_user.user_password,fetched_user.salt,user_password):
            connection.commit()
            connection.close()
            new_file(username,mode,thisfile.filename)
            save_path=os.path.join("D:\\sket\\",f"files\\{username}\\{thisfile.filename}")
            if not os.path.exists(f"D:\\sket\\files\\{username}\\"):
                os.makedirs(f"D:\\sket\\files\\{username}\\")
            with open(save_path, "wb") as f:
                f.write(await thisfile.read())
            
        else:
            connection.commit()
            connection.close()
            return {"message": "no memory of password?"}
    else:
        connection.commit()
        connection.close()
        return {"message": "this file already exist"}
    
    
@app.post("/new_user")
def new_user(data:new_user):
    try:
        connection = sqlite3.connect('Base.db')
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM Users WHERE user_name = ?""", ((data.user_name,)))
        if cursor.fetchone()==None: 
            cursor.execute("SELECT * FROM Users")
            results = cursor.fetchall()
            id = len(results)
            salt,hashed_password=salt_and_hash_password(data.password)
            cursor.execute('''INSERT INTO Users(user_id, user_name, user_password, salt)
                    VALUES(?, ?, ?, ?)''', (id, data.user_name, hashed_password, salt))
            connection.commit()
            connection.close()
            
        else:
            connection.commit()
            connection.close()
            return {"message": "this user already exist"}
        
    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)

@app.post("/rewrite_file")
async def rewrite_file(thisfile: UploadFile,username: str = Form(),user_password:str=Form()):
    try:
        connection = sqlite3.connect('Base.db')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM Users WHERE user_name = ?""", ((username,)))
        fetched_user = user(**cursor.fetchone())
        cursor.execute("""SELECT * FROM files WHERE file_name =?""", (thisfile.filename,))
        if cursor.fetchone()==None:
            connection.commit()
            connection.close()
            return {"message": "this file is not exist"}
        else:
            cursor.execute("""SELECT * FROM files WHERE file_name =?""", (thisfile.filename,))
            fetched_file=file(**cursor.fetchone())
            cursor.execute("""SELECT * FROM Users WHERE user_id = ?""", ((fetched_file.owner_user_id,)))
            owner_user=user(**cursor.fetchone())
            connection.commit()
            connection.close()
            if password_correct(fetched_user.user_password,fetched_user.salt,user_password):
                save_path=os.path.join("D:\\sket\\",f"files\\{owner_user.user_name}\\{fetched_file.file_name}")
                if fetched_file.owner_user_id==fetched_user.user_id:
                    if fetched_file.mode//100>1:
                        with open(save_path, "wb") as f:
                            f.write(await thisfile.read())
                        return {"massage":"succesful"}
                    else:
                        return {"message": "no access?"}
                else:
                    if fetched_file.mode//10%10>1:
                        group_id=group_by_user(username)
                        if group_id==fetched_file.owner_group_id:
                            with open(save_path, "wb") as f:
                                f.write(await thisfile.read())
                            return {"massage":"succesful"}
                        else:
                            if fetched_file.mode%10>1:
                                with open(save_path, "wb") as f:
                                    f.write(await thisfile.read())
                                return {"massage":"succesful"}
                            else:
                                return {"message": "no access?"}
                    else:
                            return {"message": "no access?"}
            else:
                return {"message": "no memory of password?"}
        
    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)

@app.post("/delete_file")
def delete_file(data:get_file):
    try:
        connection = sqlite3.connect('Base.db')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM Users WHERE user_name = ?""", ((data.user_name,)))
        fetched_user = user(**cursor.fetchone())
        cursor.execute("""SELECT * FROM files WHERE file_name =?""", (data.file_name,))
        if cursor.fetchone() ==None:
            connection.commit()
            connection.close()
            return {"massage":"this file is not exist"}
        else:
            cursor.execute("""SELECT * FROM files WHERE file_name =?""", (data.file_name,))
            fetched_file=file(**cursor.fetchone())
            cursor.execute("""SELECT * FROM Users WHERE user_id = ?""", ((fetched_file.owner_user_id,)))
            owner_user=user(**cursor.fetchone())
            
            if password_correct(fetched_user.user_password,fetched_user.salt,data.password):
                save_path=os.path.join("D:\\sket\\",f"files\\{owner_user.user_name}\\{fetched_file.file_name}")
                if fetched_file.owner_user_id==fetched_user.user_id:
                    if fetched_file.mode//100>1:
                        os.remove(save_path)
                        cursor.execute("""DELETE FROM files WHERE file_name = ?""", ((data.file_name,)))
                        connection.commit()
                        connection.close()
                        return {"massage":"succesful"}
                    else:
                        connection.commit()
                        connection.close()
                        return {"message": "no access?"}
                else:
                
                    if fetched_file.mode//10%10>1:
                        group_id=group_by_user(data.user_name)
                        if group_id==fetched_file.owner_group_id:
                            os.remove(save_path)
                            cursor.execute("""DELETE FROM files WHERE file_name = ?""", ((data.file_name,)))
                            connection.commit()
                            connection.close()
                            return {"massage":"succesful"}
                        else:
                            if fetched_file.mode%10>1:
                                os.remove(save_path)
                                cursor.execute("""DELETE FROM files WHERE file_name = ?""", ((data.file_name,)))
                                connection.commit()
                                connection.close()
                                return {"massage":"succesful"}
                            else:
                                connection.commit()
                                connection.close()
                                return {"message": "no access?"}
                    else:
                        connection.commit()
                        connection.close()
                        return {"message": "no access?"}
                    
            else:
                return {"message": "no memory of password?"}
            
    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)

@app.post("/get_file")
async def get_file(data:get_file):
    try:
        connection = sqlite3.connect('Base.db')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM Users WHERE user_name = ?""", ((data.user_name,)))
        fetched_user = user(**cursor.fetchone())
        cursor.execute("""SELECT * FROM files WHERE file_name =?""", (data.file_name,))
        if cursor.fetchone()==None:
            connection.commit()
            connection.close()
            return {"message": "this file is not exist"}
        else:
            fetched_file=file(**cursor.fetchone())
            cursor.execute("""SELECT * FROM Users WHERE user_id = ?""", ((fetched_file.owner_user_id,)))
            owner_user=user(**cursor.fetchone())
            connection.commit()
            connection.close()
            if password_correct(fetched_user.user_password,fetched_user.salt,data.password):
                
                if fetched_file.owner_user_id==fetched_user.user_id:
                    
                    if fetched_file.mode//100>0:
                        return FileResponse(f"files/{owner_user.user_name}/{data.file_name}",media_type="application/octet-stream",filename=f"{data.file_name}")
                    else:
                        return {"message": "no access?"}
                else:
                    group_id=group_by_user(data.user_name)
                    if group_id==fetched_file.owner_group_id:
                        
                        if fetched_file.mode//10%10>0:
                            return FileResponse(f"files/{owner_user.user_name}/{data.file_name}",media_type="application/octet-stream",filename=f"{data.file_name}")
                        else:
                            return {"message": "no access?"}
                    else:
                        if fetched_file.mode%10>0:
                            return FileResponse(f"files/{owner_user.user_name}/{data.file_name}",media_type="application/octet-stream",filename=f"{data.file_name}")
                        else:
                            return {"message": "no access?"}
                    
                    
            else:
                return {"message": "no memory of password?"}
            
    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)

@app.post("/new_svyaz")
def new_svyaz(data: new_Connections):
    connection = sqlite3.connect('Base.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""SELECT * FROM Users WHERE user_name = ?""", ((data.user_name,)))
    fetched_user = user(**cursor.fetchone())
    if password_correct(fetched_user.user_password,fetched_user.salt,data.user_password):
        connection = sqlite3.connect('Base.db')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM Users WHERE user_name = ?""", (data.user_name,))
        fetched_user = user(**cursor.fetchone())
        cursor.execute("""SELECT * FROM groups WHERE group_name = ?""", (data.group_name,))
        group = cursor.fetchone()
        cursor.execute('''INSERT INTO connections(group_id , user_id )
                    VALUES(?, ?)''', (group[0],fetched_user.user_id))
        connection.commit()
        connection.close()
        return {"massage":"succesful"}
    else:
        connection.commit()
        connection.close()
        return {"message": "no memory of password?"}


@app.post("/new_group")
def new_group(data:new_group):
    connection = sqlite3.connect('Base.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM groups")
    results = cursor.fetchall()
    cursor.execute("SELECT * FROM groups WHERE group_name = ?",(data.group_name))
    if cursor.fetchone() == None:
        id = len(results)
        cursor.execute('''INSERT INTO groups(group_id, group_name)
                        VALUES(?,?)''',( id,data.group_name))
        connection.commit()
        connection.close()
        return {"massage":"succesful"}
    else:
        connection.commit()
        connection.close()
        return {"massage":"this group already exist"}
    
@app.post("/disconnect")
def disconnect(data:new_Connections):
    connection = sqlite3.connect('Base.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""SELECT * FROM Users WHERE user_name = ?""", ((data.user_name,)))
    fetched_user = user(**cursor.fetchone())
    if password_correct(fetched_user.user_password,fetched_user.salt,data.user_password):
        connection = sqlite3.connect('Base.db')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM Users WHERE user_name = ?""", (data.user_name,))
        fetched_user = user(**cursor.fetchone())
        cursor.execute("""SELECT * FROM groups WHERE group_name = ?""", (data.group_name,))
        group = cursor.fetchone()
        cursor.execute('''DELETE FROM connections WHERE group_id = ? AND user_id = ? ''', (group[0],fetched_user.user_id))
        connection.commit()
        connection.close()
        return {"massage":"succesful"}
    else:
        connection.commit()
        connection.close()
        return {"message": "no memory of password?"}

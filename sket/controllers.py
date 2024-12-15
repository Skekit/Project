import os
import sqlite3
from fastapi import FastAPI, UploadFile, Form, Depends, HTTPException, status, Response, Cookie
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from uuid import uuid4 
from time import time
import re
from starlette.responses import FileResponse
from typing import Annotated, Mapping
from models import  New_Connections, New_group, New_user, Get_file, User,File,Group
from services import Create_connection,Create_group,Create_user,delete_connection,delete_file_by_name,Have_access_1,Have_access,password_correct,new_file,get_files_names,get_files_names_by_user
app = FastAPI()

def get_db():
    connection = sqlite3.connect('Base.db',check_same_thread=False)
    connection.row_factory = sqlite3.Row
    try:
        yield connection.cursor()
    finally:
        connection.commit()
        connection.close()

sec = HTTPBasic()

COOKIE_ALIAS = "SKET"

session_storage: Mapping[str, str] = dict()

def check_auth(credentials: Annotated[HTTPBasicCredentials, Depends(sec)], db: sqlite3.Cursor = Depends(get_db)):
    login = credentials.username
    passw = credentials.password
    exc = HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or passw", headers={"WWW_Authenticate": "Basic"})
    fetched_user = User.getByName(db, login)

    if fetched_user is None:
        raise exc
    is_correct = password_correct(fetched_user.password, fetched_user.salt, passw)
    if not is_correct:
        raise exc
    
    return fetched_user.id
    


def set_session(id):
    sessid = uuid4().hex
    while sessid in session_storage.keys():
        sessid = uuid4().hex
    session_storage[sessid] = str(id)
    return sessid


def get_session(sessid: str = Cookie(default=None, alias=COOKIE_ALIAS)):
    print(sessid)
    exc = HTTPException(status.HTTP_403_FORBIDDEN, detail="Access forbidden")
    if not sessid:
        raise exc
    if re.match(r'[a-f0-9]{32}', sessid) is None:
        raise exc
    sess = session_storage.get(sessid)
    if sess is None:
        raise exc
    
    return sess


    
def rem_session(sess_data: str = Depends(get_session), sessid: str = Cookie(default=None, alias=COOKIE_ALIAS)):
    del session_storage[sessid]
    return sess_data

@app.post('/auth/login')
def login(response: Response, auth: Annotated[str, Depends(check_auth)]):
    session_id = set_session(auth)
    response.set_cookie(COOKIE_ALIAS, session_id, expires=300)
    return {"success": True}

@app.post('/auth/check')
def check(session_id: str = Depends(get_session)):
    return {"success": True, "session": session_id}

@app.post('/auth/logout')
def login(response: Response, dropped: Annotated[str, Depends(rem_session)]):
    response.delete_cookie(COOKIE_ALIAS)
    return {"success": True, "deleted": dropped}

@app.post("/upload_file")
async def create_upload_file(thisfile: UploadFile,credentials: Annotated[HTTPBasicCredentials, Depends(sec)], mode: int = Form(), group: str = Form(), cursor: sqlite3.Cursor = Depends(get_db)):
    fetched_file=File.getByName(thisfile.filename,cursor)
    if fetched_file is None:
        fetched_user = User.getByName(cursor,credentials.username)
        if password_correct(fetched_user.password,fetched_user.salt,credentials.password):
            new_file(credentials.username,mode,thisfile.filename,cursor,group)
            cur_path=os.getcwd()
            save_path=os.path.join(f"{cur_path}",f"files\\{credentials.username}\\{thisfile.filename}")
            if not os.path.exists(f"{cur_path}\\files\\{credentials.username}\\"):
                os.makedirs(f"{cur_path}\\files\\{credentials.username}\\")
            with open(save_path, "wb") as f:
                f.write(await thisfile.read())
        else:
            return {"message": "no memory of password?"}
    else:
        return {"message": "this file already exist"}
    
    
@app.post("/new_user")
def new_user(data:New_user, cursor: sqlite3.Cursor = Depends(get_db)):
    try:
        Create_user(data.name, data.password,cursor)
        Create_group(data.name, cursor)
        Create_connection(data.name, data.name, cursor)
    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)
        return {"message": "this user already exist"}

@app.post("/rewrite_file")
async def rewrite_file(thisfile: UploadFile,credentials: Annotated[HTTPBasicCredentials, Depends(sec)], cursor: sqlite3.Cursor = Depends(get_db)):
    try:
        username=credentials.username
        user_password=credentials.password
        fetched_user = User.getByName(cursor,username)
        fetched_file=File.getByName(thisfile.filename,cursor)
        if fetched_file is None:
            return {"message": "this file is not exist"}
        else:
            owner_user=User.getById(fetched_file.owner_user_id,cursor)
            if password_correct(fetched_user.password,fetched_user.salt,user_password):
                cur_path=os.getcwd()
                save_path=os.path.join(f"{cur_path}\\",f"files\\{owner_user.name}\\{fetched_file.name}")
                if Have_access(fetched_file.mode,owner_user.id,username,fetched_user.id,fetched_file.owner_group_id,2,cursor):
                    with open(save_path, "wb") as f:
                        f.write(await thisfile.read())
                    return {"massage":"succesful"}
                else:
                    return {"message": "no access?"}
            else:
                return {"message": "no memory of password?"}
        
    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)

@app.post("/delete_file")
def delete_file(data:Get_file,credentials: Annotated[HTTPBasicCredentials, Depends(sec)], cursor: sqlite3.Cursor = Depends(get_db)):
    try:
        user_name=credentials.username
        password=credentials.password
        fetched_user = User.getByName(cursor,user_name)
        fetched_file=File.getByName(data.file_name,cursor)
        if fetched_file is None:
            return {"massage":"this file is not exist"}
        else:
            owner_user=User.getById(fetched_file.owner_user_id,cursor)
            if password_correct(fetched_user.password,fetched_user.salt,password):
                cur_path=os.getcwd()
                save_path=os.path.join(f"{cur_path}\\",f"files\\{owner_user.name}\\{fetched_file.name}")
                if Have_access(fetched_file.mode,owner_user.id,user_name,fetched_user.id,fetched_file.owner_group_id,2,cursor):
                    with open(save_path, "wb") as f:
                        os.remove(save_path)
                    delete_file_by_name(data.file_name)
                    return {"massage":"succesful"}
                else:
                    return {"message": "no access?"}
            else:
                return {"message": "no memory of password?"}
            
    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)


@app.post("/get_file")
async def get_file(file_name: str,credentials: Annotated[HTTPBasicCredentials, Depends(sec)], cursor: sqlite3.Cursor = Depends(get_db)):
    try:
        user_name=credentials.username
        password=credentials.password
        fetched_user = User.getByName(cursor,user_name)
        fetched_file=File.getByName(file_name,cursor)
        if fetched_file is None:
            return {"message": "this file is not exist"}
        else:
            owner_user=User.getById(fetched_file.owner_user_id,cursor)
            if password_correct(fetched_user.password,fetched_user.salt,password):
                if Have_access(fetched_file.mode,owner_user.id,user_name,fetched_user.id,fetched_file.owner_group_id,1,cursor):
                    return FileResponse(f"files/{owner_user.name}/{file_name}",media_type="application/octet-stream",filename=f"{file_name}")
                else:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"message": "no access?"}) 
            else:
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail={"message": "no memory of password?"})
            
    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail='Сервис временно недоступен')
    

#@app.post("/get_file1")
async def get_file1(filename: str,credentials: Annotated[HTTPBasicCredentials, Depends(sec)], auth: str = Depends(get_session), cursor: sqlite3.Cursor = Depends(get_db)):
    
    try:
        # fetched_user = User.getByName(cursor,data.user_name)
        fetched_file=File.getByName(filename,cursor)
        
        if fetched_file is None:
            return {"message": "this file is not exist"}
        else:
            owner_user=User.getById(fetched_file.owner_user_id,cursor)
            user=User.getByName(cursor,credentials.username)
            if Have_access(fetched_file.mode,owner_user.id,credentials.username,user.id,fetched_file.owner_group_id,1,cursor):
                
                return FileResponse(f"files/{owner_user.name}/{filename}",media_type="application/octet-stream",filename=f"{filename}")
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="no access?") 
                
            
    except Error as error:
        print("Ошибка при работе с SQLite", error)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail='Сервис временно недоступен')

@app.post("/new_svyaz")
def new_svyaz(data: New_Connections,credentials: Annotated[HTTPBasicCredentials, Depends(sec)], cursor: sqlite3.Cursor = Depends(get_db)):
    user_name=credentials.username
    if Create_connection(user_name,data.group_name,cursor):
        return {"massage":"succesful"}
    else:
        return {"message": "this group not exist"}
    


@app.post("/new_group")
def new_group(data:New_group, cursor: sqlite3.Cursor = Depends(get_db)):
    if Create_group(data.group_name,cursor):
        return {"massage":"succesful"}
    else:
        return {"massage":"this group already exist"}
    
@app.post("/disconnect")
def disconnect(data:New_Connections,credentials: Annotated[HTTPBasicCredentials, Depends(sec)], cursor: sqlite3.Cursor = Depends(get_db)):
    fetched_user = User.getByName(cursor,credentials.username)
    if delete_connection(data.group_name,fetched_user.id,cursor):
        return {"massage":"succesful"}
    else:
        return {"massage":"this group not exist"}
    

@app.get("/get_all_files_names")
def get_all_files_names(credentials: Annotated[HTTPBasicCredentials, Depends(sec)], cursor: sqlite3.Cursor = Depends(get_db)):
    files=get_files_names(cursor,credentials.username)
    massage_string='this is all files that you can see: '
    for file in files:
        massage_string+=(f'{file} \n ')
    return {"message": f"{massage_string}"}

@app.get("/get_files_names_from_{name}")
def get_files_names_from_user(name:str,credentials: Annotated[HTTPBasicCredentials, Depends(sec)], cursor: sqlite3.Cursor = Depends(get_db)):
    names=get_files_names_by_user(credentials.username, name,cursor)
    massage_string=f'this is all files that you can see from {name}: '
    try:
        names=names.split()
    except AttributeError as e:
        all_ok=1
    for name in names:
        massage_string+=(f'{name} \n ')
    return {"message": f"{massage_string}"}

@app.get("/get_my_groups")
def get_groups(credentials: Annotated[HTTPBasicCredentials, Depends(sec)],cursor: sqlite3.Cursor = Depends(get_db)):
    group=Group.getByUserName(credentials.username,cursor)
    list_of_groups=""
    for t in group:
        list_of_groups+=f'{t.name} \n'
    return {"message": f'there are groups you taking part in: {list_of_groups}'}
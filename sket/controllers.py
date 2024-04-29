import os
import sqlite3
from fastapi import FastAPI, UploadFile, Form, Depends, HTTPException, status
from starlette.responses import FileResponse
from models import  New_Connections, New_group, New_user, Get_file, User,File,Group
from services import Create_connection,Create_group,Create_user,delete_connection,delete_file_by_name,Have_access_1,Have_access_2,password_correct,new_file,get_files_names,get_files_names_by_user
app = FastAPI()

def get_db():
    connection = sqlite3.connect('Base.db',check_same_thread=False)
    connection.row_factory = sqlite3.Row
    try:
        yield connection.cursor()
    finally:
        connection.commit()
        connection.close()

@app.post("/upload_file")
async def create_upload_file(thisfile: UploadFile,username: str = Form(), mode: int = Form(),user_password:str=Form(), cursor: sqlite3.Cursor = Depends(get_db)):
    fetched_file=File.getByName(thisfile.filename,cursor)
    if fetched_file is None:
        fetched_user = User.getByName(cursor,username)
        if password_correct(fetched_user.password,fetched_user.salt,user_password):
            new_file(username,mode,thisfile.filename,cursor)
            cur_path=os.getcwd()
            save_path=os.path.join(f"{cur_path}",f"files\\{username}\\{thisfile.filename}")
            if not os.path.exists(f"{cur_path}\\files\\{username}\\"):
                os.makedirs(f"{cur_path}\\files\\{username}\\")
            with open(save_path, "wb") as f:
                f.write(await thisfile.read())
        else:
            return {"message": "no memory of password?"}
    else:
        return {"message": "this file already exist"}
    
    
@app.post("/new_user")
def new_user(data:New_user, cursor: sqlite3.Cursor = Depends(get_db)):
    try:
        Create_user(data.name,data.password,cursor)
    except sqlite3.Error as error:
        #print("Ошибка при работе с SQLite", error)
        return {"message": "this user already exist"}

@app.post("/rewrite_file")
async def rewrite_file(thisfile: UploadFile,username: str = Form(),user_password:str=Form(), cursor: sqlite3.Cursor = Depends(get_db)):
    try:
        fetched_user = User.getByName(cursor,username)
        fetched_file=File.getByName(thisfile.filename,cursor)
        if fetched_file is None:
            return {"message": "this file is not exist"}
        else:
            owner_user=User.getById(fetched_file.owner_user_id,cursor)
            if password_correct(fetched_user.password,fetched_user.salt,user_password):
                cur_path=os.getcwd()
                save_path=os.path.join(f"{cur_path}\\",f"files\\{owner_user.name}\\{fetched_file.name}")
                if Have_access_2(fetched_file.mode,owner_user.id,username,fetched_user.id,fetched_file.owner_group_id,cursor):
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
def delete_file(data:Get_file, cursor: sqlite3.Cursor = Depends(get_db)):
    try:
        fetched_user = User.getByName(cursor,data.user_name)
        fetched_file=File.getByName(data.file_name,cursor)
        if fetched_file is None:
            return {"massage":"this file is not exist"}
        else:
            owner_user=User.getById(fetched_file.owner_user_id,cursor)
            if password_correct(fetched_user.password,fetched_user.salt,data.password):
                cur_path=os.getcwd()
                save_path=os.path.join(f"{cur_path}\\",f"files\\{owner_user.name}\\{fetched_file.name}")
                if Have_access_2(fetched_file.mode,owner_user.id,data.user_name,fetched_user.id,fetched_file.owner_group_id,cursor):
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
async def get_file(data:Get_file, cursor: sqlite3.Cursor = Depends(get_db)):
    try:
        fetched_user = User.getByName(cursor,data.user_name)
        fetched_file=File.getByName(data.file_name,cursor)
        
        if fetched_file is None:
            return {"message": "this file is not exist"}
        else:
            owner_user=User.getById(fetched_file.owner_user_id,cursor)
            
            if password_correct(fetched_user.password,fetched_user.salt,data.password):
                if Have_access_1(fetched_file.mode,owner_user.id,data.user_name,fetched_user.id,fetched_file.owner_group_id,cursor):
                    return FileResponse(f"files/{owner_user.name}/{data.file_name}",media_type="application/octet-stream",filename=f"{data.file_name}")
                else:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"message": "no access?"}) 
                
            else:
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail={"message": "no memory of password?"})
            
    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail='Сервис временно недоступен')

@app.post("/new_svyaz")
def new_svyaz(data: New_Connections, cursor: sqlite3.Cursor = Depends(get_db)):
    fetched_user = User.getByName(cursor,data.user_name)
    if password_correct(fetched_user.password,fetched_user.salt,data.user_password):
        
        if Create_connection(data.user_name,data.group_name,cursor):
            return {"massage":"succesful"}
        else:
            return {"message": "this group not exist"}
    else:
        
        return {"message": "no memory of password?"}


@app.post("/new_group")
def new_group(data:New_group, cursor: sqlite3.Cursor = Depends(get_db)):
    if Create_group(data.group_name,cursor):
        return {"massage":"succesful"}
    else:
        return {"massage":"this group already exist"}
    
@app.post("/disconnect")
def disconnect(data:New_Connections, cursor: sqlite3.Cursor = Depends(get_db)):
    fetched_user = User.getByName(cursor,data.user_name)
    if password_correct(fetched_user.password,fetched_user.salt,data.user_password):
        if delete_connection(data.group_name,fetched_user.id,cursor):
            return {"massage":"succesful"}
        else:
            return {"massage":"this group not exist"}
    else:
        return {"message": "no memory of password?"}

@app.get("/get_all_files_names")
def get_all_files_names( cursor: sqlite3.Cursor = Depends(get_db)):
    names=get_files_names(cursor)
    massage_string=''
    try:
        names=names.split()
    except AttributeError as e:
        all_ok=1
    for name in names:
        massage_string+=(f'{name} \n ')
    return {"message": f"{massage_string}"}

@app.get("/get_files_names_from_{name}")
def get_files_names_from_user(name:str, cursor: sqlite3.Cursor = Depends(get_db)):
    names=get_files_names_by_user(name,cursor)
    massage_string=''
    try:
        names=names.split()
    except AttributeError as e:
        all_ok=1
    for name in names:
        massage_string+=(f'{name} \n ')
    return {"message": f"{massage_string}"}
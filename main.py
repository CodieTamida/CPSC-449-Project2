from fastapi import FastAPI, HTTPException, status, Depends

from models import NewAccountRequest
from http import HTTPStatus
from models import *
from helpers.db_query import *
from helpers.response import *
import sqlite3

app = FastAPI()

##### NEED FUNCTIONS: get_db, get_db_reads, verify_password, generate_claims #####

@app.get("/")
async def root():
    return {"message": "User Authentication services"}

@app.post("/register")
def register(request: NewAccountRequest, db:sqlite3.Connection = Depends(get_db)):
    
    user = get_user_by_username(request.username, db)
    
    if user: 
        raise_exception(HTTPStatus.CONFLICT, f'User with username {user["username"]} already exists')
    
    if gracefully_handle_db_transaction(create_user_sql_script(request), db):
        user = get_user_by_username(request.username, db)

        return create_response(HTTPStatus.CREATED, f'{user["username"]} created!', user)

@app.post("/login")
def login(request:LoginRequest, db: sqlite3.Connection = Depends(get_db_reads)):
    user = get_user_by_username(request.username, db, hide_password =False)

    if not user:
        raise_exception(HTTPStatus.NOT_FOUND, "User not Found")

    if not verify_password(request.password, user["password"]):
        raise_exception(HTTPStatus.UNAUTHORIZED, "Username or Password is not Valid")

    return generate_claims(user["username"], user["user_id"])
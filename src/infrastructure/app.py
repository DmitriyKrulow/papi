# pip install -r requirements.txt
# python.exe -m pip install --upgrade pip

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/db-check")
def check_db_connection():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        conn.close()
        return {"status": "connected", "database": "papiBD"}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}

@app.get("/")
def root():
    return {"message": "Hello World"}

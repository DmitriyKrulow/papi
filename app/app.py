# pip install -r requirements.txt
# python.exe -m pip install --upgrade pip

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

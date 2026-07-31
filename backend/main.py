if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.infrastructure.main:app", host="127.0.0.1", port=8888, reload=True)

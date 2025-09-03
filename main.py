import uvicorn
from fastapi import FastAPI

from api.router import api_router

app = FastAPI()

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

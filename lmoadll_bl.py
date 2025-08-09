'''
-*- coding: utf-8 -*-

lmoadll_bl platform

@copyright  Copyright (c) 2025 lmoadll_bl team
@license  GNU General Public License 3.0

'''
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from install import installRouter

app = FastAPI(
    title="lmoadll_bl",
    version="0.0.1"
)

app.include_router(installRouter, prefix="/install", tags=["install"])

@app.get("/")
async def root():
   return {"message": "Hello world"}

app.mount("/uploads", StaticFiles(directory="usr/uploads"), name="uploads")

# 有些浏览器会自动的发出请求寻找favicon.ico，由于看得不爽，于是顺便返回一个ico
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("usr/uploads/favicon.ico")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("lmoadll_bl:app", reload=True, host="0.0.0.0", port=8002, log_level="debug")

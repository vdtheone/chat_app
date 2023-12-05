from fastapi import FastAPI
from chat.routers.user import user_router
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(user_router, prefix="/chat", tags=["User"])

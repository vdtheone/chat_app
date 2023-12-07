import json
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from chat.utils.generate_jwt_token import decode_jwt_token
from chat.models.message import Message
from chat.services.dependencies import get_current_user
from chat.models.user_info import User
from chat.schemas.user import UserCreateSchema
from config import SessionLocal
from typing import List
from chat.services.user import (
    Oauth2Login,
    create_new_user,
    handle_cleanup,
    handle_disconnect,
    handle_group_chat_cleanup,
    handle_group_chat_connection,
    handle_group_chat_message,
    handle_received_message,
    handle_websocket_connection,
)

user_router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@user_router.websocket("/ws/{id}")
async def websocket_endpoint_personal_chat(
    websocket: WebSocket, id: int, db: Session = Depends(get_db)
):
    await websocket.accept()
    user_id = None

    try:
        user_id = await handle_websocket_connection(websocket, id)

        while True:
            data = await websocket.receive_text()
            await handle_received_message(data, user_id, id, db)

    except HTTPException as e:
        print("HTTP Exception: ", str(e))

    except WebSocketDisconnect:
        await handle_disconnect(user_id)

    except Exception as e:
        print("Exception: ", str(e))

    finally:
        await handle_cleanup(websocket, user_id)
        print("Finally")


@user_router.websocket("/ws/chat/group")
async def websocket_group_chat(websocket: WebSocket):
    try:
        await handle_group_chat_connection(websocket)

        while True:
            await handle_group_chat_message(websocket)

    except Exception as e:
        print(f"Error handling WebSocket communication: {str(e)}")
    finally:
        await handle_group_chat_cleanup()


# @user_router.websocket("/ws/chat/group")
# async def websocket_group_chat(websocket: WebSocket):
#     try:
#         await websocket.accept()
#         web_list.append(websocket)
#         active_connections["group"] = websocket

#         while True:
#             data = await websocket.receive_text()
#             for active_connection in active_connections:
#                 await broadcast_message(data, active_connections[active_connection])
#     except Exception as e:
#         print(f"Error handling WebSocket communication: {str(e)}")
#     finally:
#         if "group" in active_connections:
#             del active_connections["group"]


@user_router.post("/login")
async def login_(
    oauth2formdata: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    token = Oauth2Login(oauth2formdata, db)
    return token


@user_router.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@user_router.post("/create_user")
def new_user(request: Request, user: UserCreateSchema, db: Session = Depends(get_db)):
    return create_new_user(request, user, db)

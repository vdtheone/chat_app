from fastapi import HTTPException, Request, WebSocket, status
from fastapi.security import OAuth2PasswordRequestForm
from chat.models.message import Message
from chat.utils.generate_jwt_token import (
    create_jwt_token,
    decode_jwt_token,
    verify_password,
)
from chat.models.user_info import User
from chat.schemas.user import UserCreateSchema
from sqlalchemy.orm import Session


active_connections = {}
web_list = []
user_statuses = {}


def create_new_user(request: Request, user: UserCreateSchema, db: Session):
    user_exists = db.query(User).filter(User.username == user.username).first()

    if user_exists:
        raise HTTPException(status_code=403, detail="User Already Exists")

    user = User(username=user.username, email=user.email, password=user.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"Message": "User created"}


def Oauth2Login(oauth2formdata: OAuth2PasswordRequestForm, db: Session):
    user = (
        db.query(User)
        .filter(
            User.username == oauth2formdata.username,
            User.password == oauth2formdata.password,
        )
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    # if not verify_password(oauth2formdata.password, user.password):
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Incorrect username or password",
    #     )

    access_token = create_jwt_token({"id": user.id, "username": user.username})

    # pass only token because OAuth2 return token with Bearer prefix
    access_token = access_token.split()[1]

    token = {"access_token": access_token, "token_type": "bearer"}
    return token


async def handle_websocket_connection(websocket, id):
    web_list.append(websocket)
    jwt_token = websocket.headers.get("Authorization")
    user_id = decode_jwt_token(jwt_token)
    active_connections[user_id] = websocket
    status_message = {"user_id": user_id, "status": "online"}
    await websocket.send_json(status_message)
    return user_id


async def handle_received_message(data, user_id, id, db):
    if id in active_connections:
        new_message = Message(sender_id=user_id, receiver_id=id, content=data)
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        await broadcast_message(data, active_connections[id])
    else:
        new_message = Message(sender_id=user_id, receiver_id=id, content=data)
        db.add(new_message)
        db.commit()
        db.refresh(new_message)


async def handle_disconnect(user_id):
    if user_id in active_connections:
        del active_connections[user_id]


async def handle_cleanup(websocket, user_id):
    if websocket.client_state == "connected":
        del active_connections[user_id]
        await websocket.close()


async def broadcast_message(message, sender_websocket: WebSocket):
    await sender_websocket.send_text(message)


async def handle_group_chat_connection(websocket):
    await websocket.accept()
    web_list.append(websocket)
    active_connections["group"] = websocket


async def handle_group_chat_message(websocket):
    data = await websocket.receive_text()
    for active_connection_key, active_connection in active_connections.items():
        if active_connection_key != "group":
            await broadcast_message(data, active_connection)


async def handle_group_chat_cleanup():
    if "group" in active_connections:
        del active_connections["group"]

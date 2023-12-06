import json
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
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
from chat.services.user import Oauth2Login, create_new_user

user_router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


active_connections = {}
web_list = []
user_statuses = {}


async def authenticate_user(websocket: WebSocket, db: Session):
    
    jwt_token = websocket.headers.get("Authorization")
    user_id = decode_jwt_token(jwt_token)
    if user_id:
        return user_id
    else:
        raise HTTPException(status_code=401, detail="Invalid or missing token")


async def handle_websocket_communication(
    websocket: WebSocket, user_id: int, id: int, db: Session
):
    try:
        while True:
            pass
    except Exception as e:
        if user_id in active_connections:
            # user_statuses[user_id] = "offline"
            # await send_user_status_update(user_id, "offline")
            del active_connections[user_id]
    finally:
        if user_id in active_connections:
            # user_statuses[user_id] = "offline"
            # await send_user_status_update(user_id, "offline")
            del active_connections[user_id]
            await websocket.close()




async def send_user_status_update(user_id: int, status: str):
    websocket = active_connections.get(str(user_id))
    if websocket:
        # Construct and send status update message
        status_message = {"user_id": user_id, "status": status}
        await websocket.send_json(status_message)


# WebSocket disconnection event handler
async def websocket_disconnect(user_id: int):
    if user_id in active_connections:
        del active_connections[user_id]
        user_statuses[user_id] = "offline"
        await send_user_status_update(user_id, "offline")
            


@user_router.websocket("/ws/{id}")
async def websocket_endpoint_personal_chat(
    websocket: WebSocket, id: int, db: Session = Depends(get_db)
):
    await websocket.accept()
    try:
        web_list.append(websocket)
        jwt_token = websocket.headers.get("Authorization")
        user_id = decode_jwt_token(jwt_token)
        active_connections[str(user_id)] = websocket
        # user_statuses[user_id] = "online"
        status_message = {"user_id": user_id, "status": "online"}
        await websocket.send_json(status_message)  
        data = await websocket.receive_text()
        # Handle the message
        if str(id) in active_connections:
            new_message = Message(sender_id=user_id, receiver_id=id, content=data)
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            await broadcast_message(data, active_connections[str(id)])
    # except HTTPException as e:
    #     if user_id in active_connections:
    #         del active_connections[user_id]
    #     print("HTTP")
    #         # user_statuses[user_id] = "offline"
    #         # await send_user_status_update(user_id, "offline")
    except WebSocketDisconnect:
        print("===========================================")
        if str(user_id) in active_connections:  
            status_message = {"user_id": user_id, "status": "offline"}
            await websocket.send_json(status_message)
        
    except Exception as e:
        status_message = {"user_id": user_id, "status": "offline"}
        await websocket.send_json(status_message)
        if str(user_id) in active_connections:   
            del active_connections[user_id]
        print("EXCEPTIPON")
    finally:
        # breakpoint()
        if websocket.client_state == "connected":
            del active_connections[user_id]
            await websocket.close()
        # user_statuses[user_id] = "offline"
        print("Finally")

        # if user_id in active_connections:
        #     user_statuses[user_id] = "offline"
        #     await send_user_status_update(user_id, "offline")



# Check user online status
def is_user_online(user_id: int) -> bool:
    return user_id in active_connections



@user_router.websocket("/ws/chat/group")
async def websocket_group_chat(websocket: WebSocket):
    try:
        # breakpoint()
        await websocket.accept()
        web_list.append(websocket)
        active_connections['group'] = websocket

        while True:
            # Receive message from a client in the group chat
            data = await websocket.receive_text()
            for active_connection in active_connections:
                await broadcast_message(data, active_connections[active_connection])
            # Broadcast the received message to all connected clients (group chat)
    except Exception as e:
        print(f"Error handling WebSocket communication: {str(e)}")
    finally:
        if 'group' in active_connections:
            del active_connections['group']


async def broadcast_message(message, sender_websocket: WebSocket):
    await sender_websocket.send_text(message)


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


# @user_router.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     active_connections.append(websocket)

#     try:
#         while True:
#             data = await websocket.receive_text()
#             message = f"User {id(websocket)}: {data}"  # Include user identification in the message if needed

#             # Broadcast the received message to all connected clients
#             for connection in active_connections:
#                 await connection.send_text(message)
#     finally:
#         # Remove the connection from the list when the client disconnects
#         active_connections.remove(websocket)


# # HTML for chat interface
# html_content = """
# <!DOCTYPE html>
# <html>
# <head>
#     <title>FastAPI Chat</title>
# </head>
# <body>
#     <h1>FastAPI Chat</h1>
#     <div id="messages"></div>
#     <input type="text" id="message" placeholder="Type a message...">
#     <button onclick="sendMessage()">Send</button>

#     <script>
#         var ws = new WebSocket("ws://localhost:8000/chat/ws");

#         ws.onmessage = function(event) {
#             var messagesDiv = document.getElementById('messages');
#             messagesDiv.innerHTML += '<p><strong>Friend:</strong> ' + event.data + '</p>';
#         };

#         function sendMessage() {
#             var messageInput = document.getElementById('message');
#             var message = messageInput.value.trim();
#             if (message !== '') {
#                 ws.send(message);
#                 var messagesDiv = document.getElementById('messages');
#                 messagesDiv.innerHTML += '<p><strong>You:</strong> ' + message + '</p>';
#                 messageInput.value = '';
#             }
#         }
#     </script>
# </body>
# </html>
# """

# @user_router.get("/")
# async def get():
#     return HTMLResponse(html_content)

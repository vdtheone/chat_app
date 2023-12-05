from fastapi import HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from chat.utils.generate_jwt_token import create_jwt_token, verify_password
from chat.models.user_info import User
from chat.schemas.user import UserCreateSchema
from sqlalchemy.orm import Session



def create_new_user(request:Request, user:UserCreateSchema, db:Session):
    user_exists = db.query(User).filter(User.username == user.username).first()

    if user_exists:
        raise HTTPException(status_code=403, detail="User Already Exists")
    
    user = User(username=user.username, email=user.email, password=user.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"Message": "User created"}


def Oauth2Login(oauth2formdata: OAuth2PasswordRequestForm, db: Session):
    user = db.query(User).filter(User.username == oauth2formdata.username, User.password==oauth2formdata.password).first()
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
from pydantic import BaseModel


class UserCreateSchema(BaseModel):
    username : str
    password : str
    email : str

    class Config:
        from_attributes = True

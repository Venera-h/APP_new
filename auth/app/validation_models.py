from typing import Annotated
from pydantic import BaseModel, Field


LoginType = Annotated[str, Field(min_length=3, max_length=200)]
PasswordType = Annotated[str, Field(min_length=3, max_length=100)]

class BaseUser(BaseModel):
    login: LoginType
    password: PasswordType

class UserRegister(BaseUser):
    pass

class UserLogin(BaseUser):
    pass

TokenType = Annotated[str, Field()]

class TokenOut(BaseModel):
    token: TokenType
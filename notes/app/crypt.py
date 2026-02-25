from jose import jwt
import os
import datetime
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY")
TOKEN_EXPIRE_MINUTES = 60

class CryptService:
    
    context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @classmethod
    def get_hashed_password(cls, password: str) -> str:
        return cls.context.hash(password)
    
    @staticmethod
    def create_token(id_user) -> str:
        claims = {
            "sub": str(id_user),
            "exp": datetime.datetime.now() + datetime.timedelta(minutes=TOKEN_EXPIRE_MINUTES)
        }
        return jwt.encode(claims, SECRET_KEY, algorithm="HS256")
    
    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        return cls.context.verify(password, hashed_password)
    
    @staticmethod
    def decode_token(token: str) -> int|None:
        try:
            claims = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            id_user = claims.get("sub")
            return int(id_user) if id_user else None
        except:
            return None
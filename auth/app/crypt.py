import os
from passlib.context import CryptContext
from jose import jwt
import datetime

SECRET_KEY = os.getenv("SECRET_KEY")
TOKEN_EXPIRE_MINUTES = 60

#хеширование паролей и работа с JWT токенами 
class CryptService:
    #bcrypt - это алгоритм хеширования паролей 
    context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # автоматическое обновление старых хешей 

    @classmethod
    def get_hashed_password(cls, password: str) -> str:
        return cls.context.hash(password)
    #Принимает пароль -> возвращает хэш

    @staticmethod
    def create_token(id_user) -> str:
        claims = {
            "sub": str(id_user),
            "exp": datetime.datetime.now() + datetime.timedelta(minutes=TOKEN_EXPIRE_MINUTES)
        }
        return jwt.encode(claims, SECRET_KEY, algorithm="HS256")
    
    #проверка паролей: принимает обычный пароль + хэш из БД 
    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        return cls.context.verify(password, hashed_password)
    
    #Декодирование токена: принимает JWT токен, возращает ID / None
    @staticmethod
    def decode_token(token: str) -> int|None:
        try:
            claims = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = claims.get("sub")
            return int(user_id) if user_id else None
        except:
            return None
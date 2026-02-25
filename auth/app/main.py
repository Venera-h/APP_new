#Сервис аутентификации /управляем пользователями 

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from validation_models import UserRegister, UserLogin, TokenOut
from sqlalchemy.orm import Session
from database import SessionLocal, User
from crypt import CryptService
from kafka_service import kafka_service


def get_session():
    session = SessionLocal()
    try:
        yield session     
    finally:
        session.close()

app = FastAPI()

@app.get("/health")
def health(): 
    return {"status": "ok"}

# CORS (Cross-Origin Resource Sharing) - это механизм безопасности, который блокирует запросы между разными доменами/портами.
# Настройка CORS для работы с React клиентом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost", "http://localhost:8000"], #разрешенные домены
    allow_credentials=True, #Authorization заголовко, JWT токенов


    allow_methods=["*"], #methods% GET, POST, PUT, DELETE, OPTIONS 
    allow_headers=["*"], #Content-Type: application/json, Authorization: Bearer token
)

#options разршает браузеру post запросы перед основным запросом
@app.options("/api/auth/register")
def options_register():
    return {"message": "OK"}

@app.options("/api/auth/login")
def options_login():
    return {"message": "OK"}

#Регистрация новых пользователей
@app.post("/api/auth/register", response_model=TokenOut)
def register_user(user_register: UserRegister, session: Session = Depends(get_session)):
    print(f"Register attempt: {user_register.login}")
    existing_user = session.query(User).filter(User.login == user_register.login).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    
    hashed_password = CryptService.get_hashed_password(user_register.password)
    database_user = User(login=user_register.login, hashed_password=hashed_password)
    session.add(database_user)

    session.commit()
    session.refresh(database_user)
    
    id_user = database_user.id
    token = CryptService.create_token(id_user)
    
    kafka_service.publish_event('UserCreated', {
        'user_id': id_user,
        'login': user_register.login,
        'event': 'user_registered'
    })
    
    return TokenOut(token=token)

@app.get("/test-users")
def test_users(session: Session = Depends(get_session)):
    users = session.query(User).all()
    return {"users": [user.login for user in users]}

#Авторизация 
@app.post("/api/auth/login", response_model=TokenOut)
def login_user(user_login: UserLogin,
            session: Session = Depends(get_session)):
    print(f"Login attempt: {user_login.login}")
    user = session.query(User).filter(User.login == user_login.login).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not CryptService.verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = CryptService.create_token(user.id)
    return TokenOut(token=token)


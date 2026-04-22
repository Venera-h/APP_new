# Сервис аутентификации - управляет пользователями (регистрация и вход)

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

# CORS - разрешаем запросы с фронтенда на другом порту
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OPTIONS нужен браузеру для preflight-запроса перед POST
@app.options("/api/auth/register")
def options_register():
    return {"message": "OK"}

@app.options("/api/auth/login")
def options_login():
    return {"message": "OK"}

# Регистрация: хешируем пароль, сохраняем в БД, публикуем событие в Kafka, возвращаем JWT токен
@app.post("/api/auth/register", response_model=TokenOut)
def register_user(user_register: UserRegister,
                  session: Session = Depends(get_session)):
    existing_user = session.query(User).filter(User.login == user_register.login).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    hashed_password = CryptService.get_hashed_password(user_register.password)
    database_user = User(login=user_register.login, hashed_password=hashed_password)
    session.add(database_user)
    session.commit()
    session.refresh(database_user)

    token = CryptService.create_token(database_user.id)

    # Публикуем событие создания пользователя в Kafka (Задание 1)
    kafka_service.publish_event('UserCreated', {
        'user_id': database_user.id,
        'login': user_register.login,
        'event': 'user_registered'
    })

    return TokenOut(token=token)


# Авторизация: проверяем пароль, возвращаем JWT токен
@app.post("/api/auth/login", response_model=TokenOut)
def login_user(user_login: UserLogin,
               session: Session = Depends(get_session)):
    user = session.query(User).filter(User.login == user_login.login).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not CryptService.verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return TokenOut(token=CryptService.create_token(user.id))

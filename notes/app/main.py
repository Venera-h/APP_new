#Notes - это сервис для управления практическими работами (CRUD операции)
#Основные функции: Create - создание новых работ, Read - получение списка работ, Update - редактирование работ, Delete - удаление работ

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from validation_models import PracticalWorkOut, PracticalWorkCreate, PracticalWorkUpdate
from database import SessionLocal, PracticalWork
from crypt import CryptService
from sqlalchemy.orm import Session
from kafka_service import kafka_service
from uuid import UUID
from note_es import NoteEventProducer, NoteEventSourcing
import uuid


def produce(data: dict):
    kafka_service.publish_event('notes-events', data)


def get_session():
    db = SessionLocal()
    try:
        yield db    
    finally:
        db.close()

app = FastAPI()

@app.get("/health")
def health(): 
    return {"status": "ok"}

@app.post("/simple-test")
def simple_test():
    print("Simple test endpoint called")
    return {"message": "Simple test works"}

# Настройка CORS для работы с React клиентом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2 = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

def get_current_user(token: str = Depends(oauth2),
                     session: Session = Depends(get_session)) -> int:
    
    print(f"=== AUTH DEBUG ===")
    print(f"Raw token: {token}")
    print(f"Token length: {len(token) if token else 0}")
    
    if not token:
        print("ERROR: No token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        id_user = CryptService.decode_token(token)
        print(f"Decoded user ID: {id_user}")
        
        if not id_user:
            print("ERROR: Token decode returned None")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        print(f"SUCCESS: User authenticated with ID {id_user}")
        return id_user
    except Exception as e:
        print(f"ERROR: Token decode exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
def get_user_work(work_id: UUID, user_id: int, session: Session) -> PracticalWork:
    work = session.query(PracticalWork).filter(
        PracticalWork.owner_id == user_id,
        PracticalWork.id == work_id
    ).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return work

@app.options("/api/works/")
def options_works():
    return {"message": "OK"}

# EVENT SOURCING: Создание работы через события
@app.post("/api/works/", response_model=PracticalWorkOut)
def create_work(work: PracticalWorkCreate,
                id_user: int = Depends(get_current_user),
                session: Session = Depends(get_session)):
    work_id = str(uuid.uuid4())
    
    # Публикуем событие создания в Kafka (вместо прямой записи в БД)
    NoteEventProducer.produce_event('c', {
        'id': work_id,
        'title': work.title,
        'content': work.content,
        'owner_id': id_user,
        'work_name': work.work_name,
        'student': work.student,
        'variant_number': work.variant_number,
        'level_number': work.level_number,
        'submission_date': str(work.submission_date),
        'grade': work.grade
    })
    
    # Replay: восстанавливаем состояние из событий
    es = NoteEventSourcing(work_id, work.title, work.content)
    es.load()
    
    return PracticalWorkOut(
        id=UUID(work_id),
        title=work.title,
        content=work.content,
        owner_id=id_user,
        work_name=work.work_name,
        student=work.student,
        variant_number=work.variant_number,
        level_number=work.level_number,
        submission_date=work.submission_date,
        grade=work.grade
    )


# EVENT SOURCING: Получение списка с replay
@app.get("/api/works/", response_model=list[PracticalWorkOut])
def get_all_works(skip: int = 0, limit: int = 100,
                 id_user: int = Depends(get_current_user),
                 session: Session = Depends(get_session)):
    works = session.query(PracticalWork).filter(PracticalWork.owner_id == id_user).offset(skip).limit(limit).all()
    result = []
    for work in works:
        # Replay: восстанавливаем актуальное состояние из событий
        es = NoteEventSourcing(str(work.id), work.title, work.content)
        es.load()
        result.append(work)
    return result

# EVENT SOURCING: Получение одной работы с replay
@app.get("/api/works/{work_id}", response_model=PracticalWorkOut)
def get_work(work_id: UUID, 
             session: Session = Depends(get_session),
             id_user: int = Depends(get_current_user)):
    # Replay: восстанавливаем состояние из событий
    es = NoteEventSourcing(str(work_id), None, None)
    es.load()
    return get_user_work(work_id, id_user, session)

# EVENT SOURCING: Обновление через события
@app.put("/api/works/{work_id}", response_model=PracticalWorkOut)
def update_work(work_id: UUID, work_update: PracticalWorkUpdate, 
                id_user: int = Depends(get_current_user),
                session: Session = Depends(get_session)):
    work = get_user_work(work_id, id_user, session)
    
    # Replay: загружаем текущее состояние из событий
    es = NoteEventSourcing(str(work_id), work.title, work.content)
    es.load()
    
    update_data = work_update.model_dump(exclude_unset=True)
    new_title = update_data.get('title', work.title)
    new_content = update_data.get('content', work.content)
    
    # Оптимистичная блокировка: проверяем версию перед обновлением
    es.update(es._NoteEventSourcing__version__, new_title, new_content)
    
    # Публикуем событие обновления в Kafka
    NoteEventProducer.produce_event('u', {
        'id': str(work_id),
        'title': new_title,
        'content': new_content
    })
    
    for field, value in update_data.items():
        setattr(work, field, value)
    session.commit()
    session.refresh(work)
    
    return work

@app.options("/api/works/{work_id}")
def options_work_by_id(work_id: UUID):
    return {"message": "OK"}

# EVENT SOURCING: Удаление через события
@app.delete("/api/works/{work_id}")
def delete_work(work_id: UUID,
                id_user: int = Depends(get_current_user),
                session: Session = Depends(get_session)):
    work = get_user_work(work_id, id_user, session)
    
    # Публикуем событие удаления в Kafka
    NoteEventProducer.produce_event('d', {
        'id': str(work_id)
    })
    
    session.delete(work)
    session.commit()
    
    return {"message": "Work deleted successfully"}

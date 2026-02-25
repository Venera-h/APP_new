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

oauth2 = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False) #извлечение токена

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
    
def get_user_work(work_id: int, user_id: int, session: Session) -> PracticalWork:
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

@app.post("/api/works/", response_model=PracticalWorkOut)
def create_work(work: PracticalWorkCreate,
                id_user: int = Depends(get_current_user),
                session: Session = Depends(get_session)):
    print(f"Creating work for user {id_user}: {work.title}")
    print(f"Work data: {work.model_dump()}")
    database_work = PracticalWork(
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
    session.add(database_work)
    session.commit()
    session.refresh(database_work)
    print(f"Work created successfully with ID: {database_work.id}")
    
    kafka_service.publish_event('WorkCreated', {
        'work_id': database_work.id,
        'user_id': id_user,
        'title': work.title,
        'operation': 'create'
    })
    
    return database_work


@app.get("/api/works/", response_model=list[PracticalWorkOut])
def get_all_works(skip: int = 0, limit: int = 100,
                 id_user: int = Depends(get_current_user),
                 session: Session = Depends(get_session)):
    return session.query(PracticalWork).filter(PracticalWork.owner_id == id_user).offset(skip).limit(limit).all()

@app.get("/api/works/{work_id}", response_model=PracticalWorkOut)
def get_work(work_id: int, 
             session: Session = Depends(get_session),
             id_user: int = Depends(get_current_user)):
    return get_user_work(work_id, id_user, session)

@app.put("/api/works/{work_id}", response_model=PracticalWorkOut)
def update_work(work_id: int, work_update: PracticalWorkUpdate, 
                id_user: int = Depends(get_current_user),
                session: Session = Depends(get_session)):
    print(f"=== UPDATE DEBUG ===")
    print(f"Updating work ID: {work_id} for user: {id_user}")
    print(f"Update data: {work_update.model_dump(exclude_unset=True)}")
    
    work = get_user_work(work_id, id_user, session)
    print(f"Found work: {work.title}")
    
    update_data = work_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        print(f"Updating {field}: {getattr(work, field)} -> {value}")
        setattr(work, field, value)
    
    session.commit()
    session.refresh(work)
    print(f"Work updated successfully")
    
    kafka_service.publish_event('WorkUpdated', {
        'work_id': work_id,
        'user_id': id_user,
        'operation': 'update'
    })
    
    return work

@app.options("/api/works/{work_id}")
def options_work_by_id(work_id: int):
    return {"message": "OK"}

@app.delete("/api/works/{work_id}")
def delete_work(work_id: uuid.UUID,
                id_user: int = Depends(get_current_user),
                session: Session = Depends(get_session)):
    print(f"=== DELETE DEBUG ===")
    print(f"Deleting work ID: {work_id} for user: {id_user}")
    
    try:
        work = get_user_work(work_id, id_user, session)
        print(f"Found work: {work.title}")
        
        session.delete(work)
        session.commit()
        print(f"Work {work_id} deleted successfully")
        
        kafka_service.publish_event('WorkDeleted', {
            'work_id': work_id,
            'user_id': id_user,
            'operation': 'delete'
        })
        
        return {"message": "Work deleted successfully"}
    except Exception as e:
        print(f"ERROR deleting work: {e}")
        session.rollback()
        raise


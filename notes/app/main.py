# Notes - сервис управления практическими работами
# Чистый Event Sourcing: БД не используется как источник состояния.
# Все изменения публикуются в Kafka, текущее состояние получается через replay.

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from validation_models import PracticalWorkOut, PracticalWorkCreate, PracticalWorkUpdate
from crypt import CryptService
from note_es import NoteEventProducer, NoteEventSourcing
from uuid import UUID
from datetime import date
import uuid
import json
from confluent_kafka import Consumer as KConsumer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2 = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

@app.get("/health")
def health():
    return {"status": "ok"}

def get_current_user(token: str = Depends(oauth2)) -> int:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Authentication required",
                            headers={"WWW-Authenticate": "Bearer"})
    id_user = CryptService.decode_token(token)
    if not id_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token",
                            headers={"WWW-Authenticate": "Bearer"})
    return id_user

def es_to_out(es: NoteEventSourcing) -> PracticalWorkOut:
    # Конвертируем восстановленное из событий состояние в response модель
    return PracticalWorkOut(
        id=UUID(es.id),
        title=es.title,
        content=es.content,
        owner_id=es.owner_id,
        work_name=es.work_name,
        student=es.student,
        variant_number=es.variant_number,
        level_number=es.level_number,
        submission_date=date.fromisoformat(es.submission_date) if isinstance(es.submission_date, str) else es.submission_date,
        grade=es.grade
    )

@app.options("/api/works/")
def options_works():
    return {"message": "OK"}

# EVENT SOURCING: публикуем событие создания, затем сразу делаем replay для ответа
@app.post("/api/works/", response_model=PracticalWorkOut)
def create_work(work: PracticalWorkCreate,
                id_user: int = Depends(get_current_user)):
    work_id = str(uuid.uuid4())

    # Публикуем событие 'c' (create) в Kafka - это единственная запись
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

    # Replay: восстанавливаем состояние из Kafka для формирования ответа
    es = NoteEventSourcing(work_id).replay()
    return es_to_out(es)


# EVENT SOURCING: replay для каждой записи - без оптимизации, как требует задание
@app.get("/api/works/", response_model=list[PracticalWorkOut])
def get_all_works(id_user: int = Depends(get_current_user)):
    # Читаем все события из топика и собираем id работ пользователя
    seen_ids = {}
    c = KConsumer({
        'bootstrap.servers': 'broker:9092',
        'group.id': f'list-{id_user}-{uuid.uuid4()}',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    })
    c.subscribe(['operations'])
    while True:
        msg = c.poll(timeout=1.0)
        if msg is None:
            break
        if msg.error():
            break
        try:
            event = json.loads(msg.value().decode('utf-8'))
            note = event.get('note', {})
            note_id = note.get('id')
            if not note_id:
                continue
            if event['op'] == 'c' and note.get('owner_id') == id_user:
                seen_ids[note_id] = True
            elif event['op'] == 'd' and note_id in seen_ids:
                # Помечаем как удалённое
                seen_ids[note_id] = False
        except Exception:
            pass
    c.close()

    # Для каждого id делаем replay - чистый Event Sourcing без кэша
    result = []
    for note_id, active in seen_ids.items():
        if active:
            es = NoteEventSourcing(note_id).replay()
            if not es.deleted and es.exists:
                result.append(es_to_out(es))
    return result


# EVENT SOURCING: replay для получения текущего состояния одной записи
@app.get("/api/works/{work_id}", response_model=PracticalWorkOut)
def get_work(work_id: UUID, id_user: int = Depends(get_current_user)):
    # Replay: восстанавливаем состояние из всех событий
    es = NoteEventSourcing(str(work_id)).replay()
    if not es.exists or es.deleted:
        raise HTTPException(status_code=404, detail="Work not found")
    if es.owner_id != id_user:
        raise HTTPException(status_code=403, detail="Forbidden")
    return es_to_out(es)


# EVENT SOURCING: публикуем событие обновления, replay возвращает новое состояние
@app.put("/api/works/{work_id}", response_model=PracticalWorkOut)
def update_work(work_id: UUID, work_update: PracticalWorkUpdate,
                id_user: int = Depends(get_current_user)):
    # Replay: проверяем что запись существует и принадлежит пользователю
    es = NoteEventSourcing(str(work_id)).replay()
    if not es.exists or es.deleted:
        raise HTTPException(status_code=404, detail="Work not found")
    if es.owner_id != id_user:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Публикуем событие 'u' (update) только с изменёнными полями
    update_data = work_update.model_dump(exclude_unset=True)
    if 'submission_date' in update_data and update_data['submission_date']:
        update_data['submission_date'] = str(update_data['submission_date'])

    NoteEventProducer.produce_event('u', {'id': str(work_id), **update_data})

    # Replay: получаем актуальное состояние после применения нового события
    es = NoteEventSourcing(str(work_id)).replay()
    return es_to_out(es)


@app.options("/api/works/{work_id}")
def options_work_by_id(work_id: UUID):
    return {"message": "OK"}


# EVENT SOURCING: публикуем событие удаления, при replay запись помечается deleted=True
@app.delete("/api/works/{work_id}")
def delete_work(work_id: UUID, id_user: int = Depends(get_current_user)):
    # Replay: проверяем существование и права
    es = NoteEventSourcing(str(work_id)).replay()
    if not es.exists or es.deleted:
        raise HTTPException(status_code=404, detail="Work not found")
    if es.owner_id != id_user:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Публикуем событие 'd' (delete) - запись не удаляется физически, только помечается
    NoteEventProducer.produce_event('d', {'id': str(work_id)})
    return {"message": "Work deleted successfully"}

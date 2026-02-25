from sqlalchemy import Column, Integer, String, UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    login = Column(String, index=True, unique=True)
    hashed_password = Column(String)
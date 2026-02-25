from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from database_models import Base, User


engine_url = os.getenv("ENGINE_URL")

engine = create_engine(engine_url)  #создание подкючения к бд 

Base.metadata.create_all(engine) 

SessionLocal = sessionmaker(engine) #создание сеcсий
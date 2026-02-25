from sqlalchemy import Column, Integer, String, Text, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PracticalWork(Base):
    __tablename__ = "practical_works"
    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    content = Column(Text)
    owner_id = Column(Integer)
    work_name = Column(String)
    student = Column(String)
    variant_number = Column(Integer)
    level_number = Column(Integer)
    submission_date = Column(Date)
    grade = Column(Integer)
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from uuid import UUID

WorkNameType = Annotated[str, Field(min_length=1, max_length=200)]
StudentType = Annotated[str, Field(min_length=1, max_length=100)]
VariantType = Annotated[int, Field(ge=1, le=100)]
LevelType = Annotated[int, Field(ge=1, le=10)]
GradeType = Annotated[int, Field(ge=1, le=5)]

class PracticalWorkBase(BaseModel): 
    work_name: WorkNameType
    student: StudentType
    variant_number: VariantType
    level_number: LevelType
    submission_date: date
    grade: GradeType

class PracticalWorkCreate(PracticalWorkBase):
    title: str
    content: str

class PracticalWorkUpdate(BaseModel):
    work_name: WorkNameType | None = None
    student: StudentType | None = None
    variant_number: VariantType | None = None
    level_number: LevelType | None = None
    submission_date: date | None = None
    grade: GradeType | None = None
    title: str | None = None
    content: str | None = None

class PracticalWorkOut(PracticalWorkBase): 
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    content: str
    owner_id: int
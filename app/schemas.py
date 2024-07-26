from typing import List, Optional
from pydantic import BaseModel

class Admin(BaseModel):
    token: str
    email: str
    pass_word: str

class Item(BaseModel):
    data: dict
class User(BaseModel):
    id: Optional[int]
    name: str
    email: str
    phone: int
    address: str
    gender: str
    passport: str
    pass_Expiry: str
    agent: str
    single: str
    docs: List[dict]

class Country(BaseModel):
    name: str

class Application(BaseModel):
    student_id: int
    university_name: str
    program: str
    intake: str

class DropdownOptionBase(BaseModel):
    name: str
    is_checked: bool

class DropdownOptionCreate(DropdownOptionBase):
    pass

class DropdownOptionOut(DropdownOptionBase):
    id: int
    is_checked: bool

    # class Config:
    #     orm_mode = True
class AgentSchema(BaseModel):
    id: Optional[int]
    email:str
    name:str
    company_name:str
    agency_type:int
    city:int
    owner_name:str
    owner_contact:int
    state:int
    tel_phone:int
    address:str
    con_per_name:str
    con_per_phone:int
    con_per_pos:str
   
    
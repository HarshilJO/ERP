from typing import List, Optional
from pydantic import BaseModel,Field



class Item(BaseModel):
    data: dict
class User(BaseModel):
    id: Optional[int] = Field(None)
    name: str
    email: str
    phone: int
    address: str
    country:str
    state:str
    city:str
    gender: str
    passport: str
    pass_Expiry: str
    agent: str
    single: str
    docs: list

class Country(BaseModel):
    name: str

class Application(BaseModel):
    id: Optional[int] = Field(None)
    student_id: int
    Country:str
    university_name: str
    program: str
    intake: str
    program:str
    program_level: str
    
class DropdownOptionBase(BaseModel):
    id: int
    name: str
    

class DropdownOptionCreate(DropdownOptionBase):
    pass

class DropdownOptionOut(BaseModel):
    status:int
    data: List[DropdownOptionBase]
    message:str
    

    # class Config:
    #     orm_mode = True
class AgentSchema(BaseModel):
    id: Optional[int] = Field(None)
    email:str
    name:str
    company_name:str
    agency_type:str
    city:str
    owner_name:str
    owner_contact:int
    state:str
    tel_phone:int
    address:str
    con_per_name:str
    con_per_phone:int
    con_per_pos:str
   
class Credentials(BaseModel):
    id: Optional[int] = Field(None)
    is_admin:Optional[bool]=Field(None)
    email:str
    password:str
    token:Optional[str]=Field(None)

class application_status(BaseModel):
    id:int
    name:str

class Logs(BaseModel):
    id: Optional[int] = Field(None)
    operation:str
    timestamp:str
    details:str
    
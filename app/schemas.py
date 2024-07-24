from typing import List, Optional
from pydantic import BaseModel
class admin(BaseModel):
    token:str
    email:str
    pass_word:str

class user(BaseModel):
    
    name:str
    email:str
    phone:int
    address:str
    gender :str
    passport :str
    pass_Expiry:str
    agent:str
    single:str
class Country(BaseModel):
    name: str
class application(BaseModel):
    student_id:int
    university_name:str
    program:str
    intake:str
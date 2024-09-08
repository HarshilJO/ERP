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
    country_id:Optional[int]=Field(None)
    country:str
    state_id:Optional[int]=Field(None)
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
    yearly_fee: Optional[str] = Field(None)
    scholarship: Optional[str] = Field(None)
    curr: Optional[str] = Field(None)
    
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
    commission:Optional[str]=Field(None)
   
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

class ApplicationQuery(BaseModel):
    name: Optional[str] = None
    ids: Optional[List[int]] = None

class CourseSearch(BaseModel):
    global_search:Optional[str] = None
    course_name: Optional[List[str]] = None
    board: Optional[str] = None
    minimum: Optional[int] = None
    remarks: Optional[str] = None
    university_name: Optional[List[str]] = None
    fees:Optional[str]=None
    scholarship:Optional[str]=None
    study_permit:Optional[List[int]]=None


class AddUni(BaseModel):
    Country:str
    university_name:str
class csv(BaseModel):
    Agent_list:Optional[List[int]]=None
    Application_list:Optional[List[int]]

class AgentWiseStudent(BaseModel):
    agent_id:Optional[List[int]] = None
    name:Optional[str]=Field(None)


class commission_get(BaseModel):
    # Agent_list: Optional[List[int]] = None
    # application_list:Optional[List[int]]=None
    # pay_recieve:Optional[int]=None
    
    paid_status:Optional[int] = Field(None)
    agent_ids : Optional[List[int]]= None
    
class select_commission(BaseModel):
    data:Optional[List[dict]]=None
    action:bool = Field(None)
    
class change_status_fee(BaseModel):
    id:int
    password: str
    
class expense(BaseModel):
    description : str
    category : str
    sub_category : str
    cost : str
    date : str
    expendature :int

class getExpenses(BaseModel):
    data:Optional[List[dict]]=None

    # Expendature
    status:Optional[int ] = Field(None)
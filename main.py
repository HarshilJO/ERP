from fastapi import FastAPI, Depends, HTTPException, status, Request, Query
from app import models, schemas
from app.database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import desc,distinct,func
import re
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List,Optional
import json
import jwt
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime, timedelta
import pandas as pd
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust this as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# To run this code:
# Use~~ uvicorn main:app --host 26.243.124.232 --port 8080 --reload
# Use for normal loading: uvicorn main:app  --reload &&& http://127.0.0.1:8000/docs#/
# To See the output use this link: http://26.243.124.232:8080/docs#/

# Create database tables
models.Base.metadata.create_all(engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_time():
    now = datetime.now()
    formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_now



#<----Validations---->
NAME_REGEX = re.compile(r"^[a-zA-Z_]+(?: [a-zA-Z_]+)*$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PASSWORD_REGEX = re.compile(r"^(?=.[A-Za-z])(?=.\d)[A-Za-z\d]{8,}$")
PHONE_REGEX = re.compile(r"^[6-9][0-9]{9}$")
#</----Validations----/>



statuses = [
    {"id": 1, "label": "Application Created"},
    {"id": 2, "label": "Application Completed"},
    {"id": 3, "label": "Application Uploaded on CRM"},
    {"id": 4, "label": "Conditional Offer Letter"},
    {"id": 5, "label": "On Hold"},
    {"id": 6, "label": "Finance Approved"},
    {"id": 7, "label": "GTE Submitted"},
    {"id": 8, "label": "GTE Approved"},
    {"id": 9, "label": "Full Offer"},
    {"id": 10, "label": "Fees Paid"},
    {"id": 11, "label": "COE Issued"},
    {"id": 12, "label": "Visa Lodged"},
    {"id": 13, "label": "Visa Approved"},
    {"id": 14, "label": "Application Withdrawn"},
    {"id": 15, "label": "Rejected by University"},
    {"id": 16, "label": "Visa Refusal"},
    {"id": 17, "label": "Visa Withdrawn"},
    {"id": 18, "label": "Visa Unidentified"},
    {"id": 19, "label": "Refund Applied"},
    {"id": 20, "label": "Refund Processed"},
    {"id": 21, "label": "Pending document"}
]
# Address details
def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)

data = load_json('address/countries.json')

@app.get("/countries")
async def get_countries():
    return {'status': 200, 'data': [{"id": country["id"], "name": country["name"]} for country in data], 'message': 'Success'}

@app.get("/countries/{country_id}/states")
async def get_states(country_id: int):
    for country in data:
        if country["id"] == country_id:
            if "states" in country:
                return {'status': 200, 'data': [{"id": state["id"], "name": state["name"]} for state in country["states"]], 'message': 'Success'}
            else:
                return {'status': 404, 'data': [], 'message': 'No states found for this country'}
    raise HTTPException(status_code=404, detail="Country not found")

@app.get("/states/{state_id}/cities")
async def get_cities(state_id: int):
    for country in data:
        if "states" in country:
            for state in country["states"]:
                if state["id"] == state_id:
                    if "cities" in state:
                        return {'status': 200, 'data': [{"id": city["id"], "name": city["name"]} for city in state["cities"]], 'message': 'Success'}
                    else:
                        return {'status': 404, 'data': [], 'message': 'No cities found for this state'}
    raise HTTPException(status_code=404, detail="State not found")

# Docs Dropdown
@app.post("/docs/", response_model=schemas.DropdownOptionOut)
async def create_option(option: schemas.DropdownOptionCreate, db: Session = Depends(get_db)):
    db_option = models.DocsDropdown(name=option.name)
    db.add(db_option)
    db.commit()
    db.refresh(db_option)
    return db_option

@app.get("/docs/")
async def read_options(db: Session = Depends(get_db)):
    options = db.query(models.DocsDropdown).all()
    return {'status': 200, 'data': options, 'message': 'Success'}
@app.get("/application/status")
async def application_status(   ):
    statuses = [
    {"id": 1, "label": "Application Created"},
    {"id": 2, "label": "Application Completed"},
    {"id": 3, "label": "Application Uploaded on CRM"},
    {"id": 4, "label": "Conditional Offer Letter"},
    {"id": 5, "label": "On Hold"},
    {"id": 6, "label": "Finance Approved"},
    {"id": 7, "label": "GTE Submitted"},
    {"id": 8, "label": "GTE Approved"},
    {"id": 9, "label": "Full Offer"},
    {"id": 10, "label": "Fees Paid"},
    {"id": 11, "label": "COE Issued"},
    {"id": 12, "label": "Visa Lodged"},
    {"id": 13, "label": "Visa Approved"},
    {"id": 14, "label": "Application Withdrawn"},
    {"id": 15, "label": "Rejected by University"},
    {"id": 16, "label": "Visa Refusal"},
    {"id": 17, "label": "Visa Withdrawn"},
    {"id": 18, "label": "Visa Unidentified"},
    {"id": 19, "label": "Refund Applied"},
    {"id": 20, "label": "Refund Processed"},
    {"id": 21, "label": "Pending document"}
]

    return {"response": 200, "data": statuses, "message":"Success"}
@app.post("/application_status_update")
async def app_status_update(app_status:schemas.application_status,db: Session = Depends(get_db)):


    db_user = db.query(models.Application).filter(models.Application.id == app_status.id).first()
    db_user.status = app_status.name
    db.commit()
    db.refresh(db_user)
    return {"response": 200, "data": 'Application Status Updated', "message": "Application Status Updated"}

#<----Login---->
def create_access_token(data: dict):
    to_encode = data.copy()
    SECRET_KEY = "09d25e094faa****************f7099f6f0f4caa6cf63b88e8d3e7"
 
# encryption algorithm
    ALGORITHM = "HS256"
    # expire time of the token
    expire = datetime.utcnow() + timedelta(minutes=3650)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
     
    # return the generated token
    return encoded_jwt
@app.post("/login")
def login(user: schemas.Credentials,db: Session = Depends(get_db)):
    db_user = db.query(models.Credentials).filter(models.Credentials.email == user.email).first()
    if db_user:
        if db_user.password == user.password:
            if db_user.is_admin:
                position='Admin'
            else:
                position='Employee'
            data = {
                'Role': position,
                'email': user.email
            }
            token = create_access_token(data=data)
            return {'status': 200, 'message': 'Login Successfull','data': json.loads(json.dumps(({"role":position,"email":user.email, "token":token})))}

        else:
            return {'status': 200, 'message': 'Incorrect Password'}
    else:
       
        return {'status': 200,'data':'User Not found    ','message': 'User Not found'}
#</----Login----/>


#<----Dashboard----->
@app.get("/Dashboard/")
async def Dashboard( db: Session = Depends(get_db)):
    timestamps=db.query(models.Application.timestamp).all()
    timestamps = [t[0] for t in timestamps]
    df = pd.DataFrame(timestamps, columns=['timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.month
    month_counts = df['month'].value_counts().sort_index()
    month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
                   7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    month_counts.index = month_counts.index.map(month_names)
    radialBar = [{"label": month, "series": count} for month, count in month_counts.items()]
    result=db.query(models.User.agent,func.count(models.User.id)).group_by(models.User.agent).all()
    donut=[]
    for agent,count in result:
        donut.append({"label":agent,"series":count})
    # print(donut)
    # print(month_counts)
    Student_data = db.query(models.User).order_by(desc(models.User.id)).limit(6).all()
    count_student=db.query(models.User).count()
    count_application=db.query(models.Application).count()
    count_agent=db.query(models.agent_data).count()
    count_pending_application = db.query(models.Application).filter(models.Application.status != "Application Completed").count()
    count_done_application = db.query(models.Application).filter(models.Application.status == "Application Completed").count()
    total_count={"student_count":count_student,
         "Application_count":count_application,
         "Agent_count":count_agent,
         "Application_Completed":count_done_application,
         "Application_Incomplete": count_pending_application,
         "RadialBar":radialBar,
         "donut":donut,
         "data":Student_data

         }
    return {'status': 200, 'data':total_count , 'message': 'Success'}
#</----Dashboard----/>



#<----Student Detils---->
@app.get("/users/")
async def read_users(name: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if name:
        user_data = db.query(models.User).filter(models.User.name.ilike(f"%{name}%")).all()
       
        if not user_data:
            return {'status': 200, 'data': [], 'message': 'Success'}
    else:
        user_data = db.query(models.User).all()
   
    return {'status': 200, 'data': user_data, 'message': 'Success'}

@app.get("/user_name")
async def user_name(db: Session = Depends(get_db)):
    agent_names = db.query(models.User.id, models.User.name).all()
    agents_list = [{"id": id, "name": name} for id, name in agent_names]
    return {'status': 200, 'data': agents_list, 'message': 'Success'}
@app.get("/users/{id}")
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
    return {'status': 200, 'data': user, 'message': 'Success'}
# User creation or update endpoint
async def get_role_from_token(request: Request):
    headers = dict(request.headers)
    token_with_bearer = headers.get("authorization")
    if not token_with_bearer:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    final_token = token_with_bearer.replace("Bearer ", "")
    payload = jwt.decode(final_token, options={"verify_signature": False})
    role_name = payload.get("Role")
    if not role_name:
        raise HTTPException(status_code=400, detail="Role not found in token")
   
    return role_name



# Log apply



@app.get("/logs/")
async def get_logs(db: Session = Depends(get_db)):
    logs = db.query(models.Logs).order_by(desc(models.Logs.id)).limit(4).all()
    return {'status': 200, 'data': logs, 'message': 'Success'}
 




@app.post("/users/")
async def create_or_update_user(user: schemas.User, request:Request,db: Session = Depends(get_db)):
    role_name = await get_role_from_token(request)

    phone_str = str(user.phone)
    # Validate phone number as a string
    a = re.fullmatch(r'[6-9][0-9]{9}', phone_str)
    if not NAME_REGEX.match(user.name):
        return {'status': 400,  'message': 'Invalid Name'}
    if not EMAIL_REGEX.match(user.email):
        return {'status': 400,  'message': 'Invalid Email'}
    if not PHONE_REGEX.match(phone_str):
        raise HTTPException(status_code=400, detail='Invalid Phone Number')

    if user.id and user.id > 0:
        db_user = db.query(models.User).filter(models.User.id == user.id).first()
        if db_user:
            # Update existing user


            new_log = models.Logs(
                operation="Updated",    
                timestamp=get_time(),
                details = f"Student {db_user.name} is Updated"
            )
            db.add(new_log)
            for key, value in user.dict(exclude_unset=True).items():
                setattr(db_user, key, value)
            db_user.logged_by = role_name
            db.commit()
            db.refresh(db_user)
            db.refresh(new_log)
           
            return {'status': 200, 'data': db_user, 'message': 'Success'}
    # Create new user
    db_user = models.User(**user.dict(exclude={"id"}),logged_by=role_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    new_log = models.Logs(
                operation="Created",    
                timestamp=get_time(),
                details = f"Student {db_user.name} Created"
            )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return {'status': 200,  'message': 'Success'}

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {'status': 204, 'data':'Student Deleted','message': 'Student  Deleted'}
#</----Student Details----/>
@app.get("/agent_name")
async def agent_name(db: Session = Depends(get_db)):
    agent_names = db.query(models.agent_data.id, models.agent_data.name).all()
    agents_list = [{"id": id, "name": name} for id, name in agent_names]
    return {'status': 200, 'data': agents_list, 'message': 'Success'}
# Agent Details
@app.get("/agent")
async def get_all_agent(name: Optional[str] = Query(None),db: Session = Depends(get_db)):

    if name:
        agents = db.query(models.agent_data).filter(models.agent_data.name.ilike(f"%{name}%")).all()
       
        if not agents:
            return {'status': 200, 'data': [], 'message': 'Success'}
    else:
        agents = db.query(models.agent_data).all()
    return {'status': 200, 'data': agents, 'message': 'Success'}

@app.post("/agents/")
async def CU_agent(request: Request,agent: schemas.AgentSchema, db: Session = Depends(get_db)):
    headers = dict(request.headers)
    token_withBearer=headers["authorization"]
    final_token=token_withBearer.replace("Bearer ", "")
    payload = jwt.decode(final_token, options={"verify_signature": False})
   
    if agent.id and agent.id > 0:
        db_agent = db.query(models.agent_data).filter(models.agent_data.id == agent.id).first()
        if db_agent:
            # Update existing agent

            new_log = models.Logs(
                operation="Updated",    
                timestamp=get_time(),
                details = f"Agent {db_agent.name} is Updated"
            )
            db.add(new_log)
            for key, value in agent.dict(exclude_unset=True).items():
                setattr(db_agent, key, value)
           
         
            db.commit()
            db.refresh(db_agent)
            db.refresh(new_log)
            return {'status': 200,'data':db_agent ,'message': 'Agent Details Updated'}
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
    else:
        # Create new agent without an id
        new_agent = models.agent_data(**agent.dict(exclude={"id"}))
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)

        new_log = models.Logs(
                operation="Created",    
                timestamp=get_time(),
                details = f"New agent {new_agent.name} is Created"
            )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return {'status': 200,'data':new_agent , 'message': 'New Agent Created'}

@app.delete("/agent_delete/{id}")
async def delete_agent(id: int, db: Session = Depends(get_db)):
    user = db.query(models.agent_data).filter(models.agent_data.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent Not Found")
    db.delete(user)
    db.commit()
    return {'status': 200, 'data': 'Agent Deleted', 'message': 'Agent Deleted'}
#<----Applications---->
uni_data = load_json('address/universities.json')
@app.get("/universities/{uni_name}")
async def get_states(uni_name: str):
    data = []
    count = 0
    for uni in uni_data:
        if uni["country"] == uni_name:
            count += 1
            university_name = uni["name"].upper()
            university_data = {
                "id": count,
                "name": university_name
            }
            data.append(university_data)
   
    # If universities are found, return them
    if data:
        return {
            'status': 200,
            'data': data,
            'message': 'Universities Found'
        }
    else:
        # If no universities are found
        return {
            'status': 404,
            'data': [],
            'message': 'No Universities Found in this Country'
        }
# Get all applications
@app.get("/application/{id}")
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.Application).filter(models.Application.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicaion Not Found")
    return {'status': 200, 'data': user, 'message': 'Success'}


# @app.get("/application")
# async def get_all_applications(name: Optional[str] = Query(None), ids: Optional[List[int]] = Query(default=None),db: Session = Depends(get_db)):

#     if ids:
#         final_result=[]

#         for id in ids:
#             for j in statuses:
#                 if id == j["id"]:
#                   final_result.append(db.query(models.Application).filter(models.Application.status == j["label"] ).all())
       
#         return {'status': 200, 'data': final_result, 'message': 'Application not found'}


#     if name:
#         agents = db.query(models.Application).filter(models.Application.student_name.ilike(f"%{name}%") ).all()
#         if not agents:
#             return {'status': 200, 'data': [], 'message': 'Application not found'}
#     else:
#         agents = db.query(models.Application).all()
#     return {'status': 200, 'data': agents, 'message': 'Success'}
@app.post("/application_get")
async def get_all_applications(query:schemas.ApplicationQuery, db: Session = Depends(get_db)):
    final_result = []

    if query.ids:
        for id in query.ids:
            for j in statuses:
                if id == j["id"]:
                    final_result.extend(db.query(models.Application).filter(models.Application.status == j["label"]).all())
        
        return {'status': 200, 'data': final_result, 'message': 'Applications fetched successfully'}

    if query.name:
        agents = db.query(models.Application).filter(models.Application.student_name.ilike(f"%{query.name}%")).all()
        if not agents:
            return {'status': 200, 'data': [], 'message': 'Application not found'}
    else:
        agents = db.query(models.Application).all()

    return {'status': 200, 'data': agents, 'message': 'Success'}

@app.post("/application")
async def CU_Applications(application: schemas.Application,request:Request, db: Session = Depends(get_db)):
    role_name = await get_role_from_token(request)
    user = db.query(models.User).filter(models.User.id == application.student_id).first()

    if user:
        rent_time = datetime.utcnow()
        current_time=rent_time.strftime('%Y-%m-%d %H:%M:%S')
        if application.id and application.id > 0:
            db_application = db.query(models.Application).filter(models.Application.id == application.id).first()
            if db_application:
                # Update existing application
                for key, value in application.dict(exclude_unset=True).items():
                    setattr(db_application, key, value)
                new_log = models.Logs(
                operation="Created",    
                timestamp=get_time(),
                details = f"New Application Created for <b>{user.name}</b> by <b>{role_name}</b>")
                db.add(new_log)
               
                # Set the student_name from the User table
                db_application.student_name = user.name
                db_application.timestamp=current_time
                db.commit()
                db.refresh(db_application)
                db.refresh(new_log)
                return {'status': 200, 'data': db_application, 'message': 'Application details updated'}
            else:
                raise HTTPException(status_code=404, detail="Application not found")
        else:
            # Create new application without an id
            new_application = models.Application(**application.dict(exclude={"id"}))
            new_application.status="Application Created"
            # Set the student_name from the User table
            new_application.student_name = user.name
            new_application.timestamp=current_time
            db.add(new_application)
            db.commit()
            db.refresh(new_application)

            new_log = models.Logs(
                operation="Created",    
                timestamp=get_time(),
                details = f"New Application Created for <b>{user.name}</b> by <b>{role_name}</b>"
            )
            db.add(new_log)
            db.commit()
            db.refresh(new_log)
           
            return {'status': 200, 'data':'New Application Created', 'message': 'New application created'}
    else:
        return {'status': 404, 'data': 'No student with given ID', 'message': 'No student with given ID'}


@app.delete("/application_delete/{id}")
async def delete_application(id: int, db: Session = Depends(get_db)):
    Application = db.query(models.Application).filter(models.Application.id == id).first()
    if not Application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application Not Found")
    db.delete(Application)
    db.commit()
    return {'status': 204,'data':'Application Deleted','message': 'Application Deleted'}
#</----Applications/---->\

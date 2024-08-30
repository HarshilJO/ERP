from fastapi import FastAPI, Depends, HTTPException, status, Request, Query,Response
from app import models, schemas
from app.database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, distinct, func, or_
import re
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import jwt
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import logging
import openpyxl
from datetime import datetime, timedelta
import pandas as pd
import pytz
from io import BytesIO
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
    original_tz = pytz.timezone('Asia/Kolkata')
    datetime_object = datetime.now(original_tz)
    current_time = datetime_object.strftime('%Y-%m-%d %H:%M:%S')
    return current_time


# <----Validations---->
NAME_REGEX = re.compile(r"^[a-zA-Z_]+(?: [a-zA-Z_]+)*$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PASSWORD_REGEX = re.compile(r"^(?=.[A-Za-z])(?=.\d)[A-Za-z\d]{8,}$")
PHONE_REGEX = re.compile(r"^[6-9][0-9]{9}$")
# </----Validations----/>

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
    {"id": 13, "label": "Visa Granted"},
    {"id": 14, "label": "Application Withdrawn"},
    {"id": 15, "label": "Rejected by University"},
    {"id": 16, "label": "Visa Refusal"},
    {"id": 17, "label": "Visa Withdrawn"},
    {"id": 18, "label": "Visa Unidentified"},
    {"id": 19, "label": "Refund Applied"},
    {"id": 20, "label": "Refund Processed"},
    {"id": 21, "label": "Pending document"}
]


async def get_role_from_token(request: Request):
    headers = dict(request.headers)
    token_with_bearer = headers.get("authorization")
    if not token_with_bearer:
        data = {'message': "Not Found",
                'data': "Not found"}
        return JSONResponse(
            status_code=404,
            content=data
        )
    final_token = token_with_bearer.replace("Bearer ", "")
    payload = jwt.decode(final_token, options={"verify_signature": False})
    role_name = payload.get("Role")
    if not role_name:
        data = {'message': "Not Found",
                'data': "Not found"}
        return JSONResponse(
            status_code=404,
            content=data
        )

    return role_name
# Address details
def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)


data = load_json('address/countries.json')


@app.get("/countries")
async def get_countries():
    return {'status': 200, 'data': [{"id": country["id"], "name": country["name"]} for country in data],
            'message': 'Success'}


@app.get("/countries/{country_id}/states")
async def get_states(country_id: int):
    for country in data:
        if country["id"] == country_id:
            if "states" in country:
                return {'status': 200,
                        'data': [{"id": state["id"], "name": state["name"]} for state in country["states"]],
                        'message': 'Success'}
            else:
                return {'status': 404, 'data': [], 'message': 'No states found for this country'}


@app.get("/states/{state_id}/cities")
async def get_cities(state_id: int):
    for country in data:
        if "states" in country:
            for state in country["states"]:
                if state["id"] == state_id:
                    if "cities" in state:
                        return {'status': 200,
                                'data': [{"id": city["id"], "name": city["name"]} for city in state["cities"]],
                                'message': 'Success'}
                    else:
                        return {'status': 404, 'data': [], 'message': 'No cities found for this state'}


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
async def application_status():
    return {"response": 200, "data": statuses, "message": "Success"}


@app.post("/application_status_update")
async def app_status_update(app_status: schemas.application_status, db: Session = Depends(get_db)):
    db_user = db.query(models.Application).filter(models.Application.id == app_status.id).first()
    db_user.status = app_status.name
    db.commit()
    db.refresh(db_user)
    return {"response": 200, "data": 'Application Status Updated', "message": "Application Status Updated"}


# <----Login---->
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
def login(user: schemas.Credentials, db: Session = Depends(get_db)):
    db_user = db.query(models.Credentials).filter(models.Credentials.email == user.email).first()
    if db_user:
        if db_user.password == user.password:
            if db_user.is_admin:
                position = 'Admin'
            else:
                position = 'Employee'
            data = {
                'Role': position,
                'email': user.email
            }
            token = create_access_token(data=data)
            content = {'message': "Login Successfull",
                       'data': json.loads(json.dumps(({"role": position, "email": user.email, "token": token})))

                       }

            response = JSONResponse(
                status_code=200,
                content=content
            )
            response.headers["Authorization"] = f"Bearer {token}"
            return response

        # elif  db_user.password != user.password:
        #         # new_dic={'message':'Incorrect Password or Username','data':'Incorrect Password or Username'}
        #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Incorrect Password" ,message='Incorrect Password',data='Incorrect Password or username')
        elif db_user.password != user.password:
            data = {'message': "Incorrect username or password",
                    'data': "Incorrect username or password"}
            return JSONResponse(
                status_code=404,
                content=data
            )
    else:
        data = {'message': "Incorrect username or password",
                'data': "Incorrect username or password"}
        return JSONResponse(
            status_code=404,
            content=data
        )


# </----Login----/>


# <----Dashboard----->
@app.get("/Dashboard/")
async def Dashboard(db: Session = Depends(get_db)):
    timestamps = db.query(models.Application.timestamp).all()
    timestamps = [t[0] for t in timestamps]
    df = pd.DataFrame(timestamps, columns=['timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.month
    month_counts = df['month'].value_counts().sort_index()
    month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
                   7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    month_counts.index = month_counts.index.map(month_names)
    radialBar = [{"label": month, "series": count} for month, count in month_counts.items()]
    result = db.query(models.User.agent, func.count(models.User.id)).group_by(models.User.agent).all()
    donut = []
    for agent, count in result:
        donut.append({"label": agent, "series": count})
    # print(donut)
    # print(month_counts)
    Student_data = db.query(models.User).order_by(desc(models.User.id)).limit(6).all()
    count_student = db.query(models.User).count()
    count_application = db.query(models.Application).count()
    count_agent = db.query(models.agent_data).count()
    count_pending_application = db.query(models.Application).filter(
        models.Application.status != "Application Completed").count()
    count_done_application = db.query(models.Application).filter(
        models.Application.status == "Application Completed").count()
    total_visa_granted = db.query(models.Application).filter(models.Application.status == "Visa Granted").count()
    total_count = {"student_count": count_student,
                   "Application_count": count_application,
                   "Agent_count": count_agent,
                   "Application_Completed": count_done_application,
                   "Application_Incomplete": count_pending_application,
                   "RadialBar": radialBar,
                   "donut": donut,
                   "data": Student_data,
                   "visa": total_visa_granted

                   }
    return {'status': 200, 'data': total_count, 'message': 'Success'}


# </----Dashboard----/>

class AgentWiseStudent(BaseModel):
    agent_id:Optional[List[int]]=None


@app.post("/student")
async def read_users(student: schemas.AgentWiseStudent, db: Session = Depends(get_db)):
    agentWiseStudent = []
    response = []
    final_result_with_search = []
    name = student.name

    agent_ids = student.agent_id
    if student.agent_id:
        for id in agent_ids:
            agent_name = db.query(models.agent_data).filter(models.agent_data.id == id).all()
            agentWiseStudent.append(agent_name[0].name.replace(" ", "").lower())
            # print(agentWiseStudent)

        # getting students with that agent
        for agent_name in agentWiseStudent:
            students = db.query(models.User).all()
            matched_students = [student for student in students if student.agent.replace(" ", "").lower() == agent_name]
            response.append(matched_students)

        if student.agent_id and name:
            user_data = db.query(models.User).filter(models.User.name.ilike(f"%{name}%")).all()

            for agent_name in agentWiseStudent:
                for student in user_data:
                    if student.agent.replace(" ", "").lower() == agent_name:
                        # print(agent_name)
                        final_result_with_search.append(student)

            return {'status': 200, 'data': final_result_with_search, 'message': 'Success'}

        return {'status': 200, 'data': [item for row in response for item in row], 'message': 'Success'}
    else:
        student_info = []

        if name:
            user_data = db.query(models.User).filter(models.User.name.ilike(f"%{name}%")).all()
            if not user_data:
                return {'status': 200, 'data': [], 'message': 'Success'}
            else:
                return {'status': 200, 'data': user_data, 'message': 'Success'}

        else:
            user_data = db.query(models.User).all()
            student_info.extend(user_data)
            return {'status': 200, 'data': student_info, 'message': 'Success'}
@app.get("/user_name")
async def user_name(db: Session = Depends(get_db)):
    agent_names = db.query(models.User.id, models.User.name).all()
    agents_list = [{"id": id, "name": name} for id, name in agent_names]
    return {'status': 200, 'data': agents_list, 'message': 'Success'}


@app.get("/users/{id}")
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        data = {'message': "Not Found",
                'data': "Not found"}
        return JSONResponse(
            status_code=404,
            content=data
        )
    return {'status': 200, 'data': user, 'message': 'Success'}


# User creation or update endpoint


# Log apply


@app.get("/logs/")
async def get_logs(db: Session = Depends(get_db)):
    logs = db.query(models.Logs).order_by(desc(models.Logs.id)).limit(4).all()
    return {'status': 200, 'data': logs, 'message': 'Success'}


def get_countriesid(data, country_name):
    for country in data:
        if country['name'] == country_name:
            return country['id']
    return None  # Return None if the country name is not found


def get_statesids(data, country_name, state_name):
    for country in data:
        if country['name'] == country_name:
            # If the country name matches, loop through the states in that country
            for state in country['states']:
                if state['name'] == state_name:
                    return state['id']
    return None  # Return None if the state name is not found within the given country


@app.post("/users/")
async def create_or_update_user(user: schemas.User, request: Request, db: Session = Depends(get_db)):
    state_name = user.state
    country_name = user.country
    role_name = await get_role_from_token(request)
    country_ids = get_countriesid(data, country_name)
    state_ids = get_statesids(data, country_name, state_name)

    # print(country_ids)

    phone_str = str(user.phone)
    # Validate phone number as a string
    a = re.fullmatch(r'[6-9][0-9]{9}', phone_str)
    if not NAME_REGEX.match(user.name):
        return {'status': 400, 'message': 'Invalid Name'}
    if not EMAIL_REGEX.match(user.email):
        return {'status': 400, 'message': 'Invalid Email'}
    if not PHONE_REGEX.match(phone_str):
        return {'status': 400, 'message': 'Invalid Number'}

    if user.id and user.id > 0:
        db_user = db.query(models.User).filter(models.User.id == user.id).first()
        if db_user:
            # Update existing user
            new_log = models.Logs(
                operation="Updated",
                timestamp=get_time(),
                details=f"Student {db_user.name} is Updated"
            )
            db.add(new_log)
            for key, value in user.dict(exclude_unset=True).items():
                setattr(db_user, key, value)
            db_user.logged_by = role_name
            db_user.country_id = country_ids
            db_user.state_id = state_ids
            db.commit()
            db.refresh(db_user)
            db.refresh(new_log)

            return {'status': 200, 'data': db_user, 'message': 'Success'}
    # Create new user
    db_user = models.User(**user.dict(exclude={"id"}), logged_by=role_name)
    db_user.country_id = country_ids
    db_user.state_id = state_ids
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    new_log = models.Logs(
        operation="Created",
        timestamp=get_time(),
        details=f"Student {db_user.name} Created"
    )

    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return {'status': 200, 'message': 'Success'}


@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        data = {'message': "Not Found",
                'data': "Not found"}
        return JSONResponse(
            status_code=404,
            content=data
        )
    db.delete(db_user)
    db.commit()
    return {'status': 204, 'data': 'Student Deleted', 'message': 'Student  Deleted'}


# </----Student Details----/>
@app.get("/agent_name")
async def agent_name(db: Session = Depends(get_db)):
    agent_names = db.query(models.agent_data.id, models.agent_data.name).all()
    agents_list = [{"id": id, "name": name} for id, name in agent_names]
    return {'status': 200, 'data': agents_list, 'message': 'Success'}


# Agent Details
def get_stateids(country_data, state_names):
    state_ids = []
    for name_tuple in state_names:
        state_name = name_tuple[0]
        for country in country_data:
            for state in country.get("states", []):
                if state["name"].lower() == state_name.lower():
                    state_ids.append(state["id"])
                    break
    return state_ids


@app.post("/agent")
async def get_all_agent(query: schemas.ApplicationQuery, db: Session = Depends(get_db)):
    agent_info = []
    if query.name:
        agents = db.query(models.agent_data).filter(models.agent_data.name.ilike(f"%{query.name}%")).all()
        if not agents:
            return {'status': 200, 'data': [], 'message': 'Agent not found'}
        else:
            return {'status': 200, 'data': agents, 'message': 'Agent found'}
    else:
        agents = db.query(models.agent_data).all()
        agent_info.extend(agents)
        state_name = db.query(models.agent_data.state).all()
        state_id = get_stateids(data, state_name)
        for id in state_id:
            for item in agent_info:
                item.__dict__['state_id'] = id
    return {'status': 200, 'data': agent_info, 'message': 'Success'}


@app.post("/agents/")
async def CU_agent(request: Request, agent: schemas.AgentSchema, db: Session = Depends(get_db)):
    headers = dict(request.headers)
    token_withBearer = headers["authorization"]
    final_token = token_withBearer.replace("Bearer ", "")
    payload = jwt.decode(final_token, options={"verify_signature": False})

    if agent.id and agent.id > 0:
        db_agent = db.query(models.agent_data).filter(models.agent_data.id == agent.id).first()
        if db_agent:
            # Update existing agent

            new_log = models.Logs(
                operation="Updated",
                timestamp=get_time(),
                details=f"Agent {db_agent.name} is Updated"
            )
            db.add(new_log)
            for key, value in agent.dict(exclude_unset=True).items():
                setattr(db_agent, key, value)

            db.commit()
            db.refresh(db_agent)
            db.refresh(new_log)
            return {'status': 200, 'data': "Agent Details Updated", 'message': 'Agent Details Updated'}
        else:
            data = {'message': "Not Found",
                    'data': "Not found"}
            return JSONResponse(
                status_code=404,
                content=data
            )
    else:
        # Create new agent without an id
        new_agent = models.agent_data(**agent.dict(exclude={"id"}))
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)

        new_log = models.Logs(
            operation="Created",
            timestamp=get_time(),
            details=f"New agent {new_agent.name} is Created"
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return {'status': 200, 'data': 'New Agent Created', 'message': 'New Agent Created'}


@app.delete("/agent_delete/{id}")
async def delete_agent(id: int, db: Session = Depends(get_db)):
    user = db.query(models.agent_data).filter(models.agent_data.id == id).first()
    if not user:
        data = {'message': "Not Found",
                'data': "Not found"}
        return JSONResponse(
            status_code=404,
            content=data
        )
    db.delete(user)
    db.commit()
    return {'status': 200, 'data': 'Agent Deleted', 'message': 'Agent Deleted'}


# <----Applications---->
uni_data = load_json('address/universities.json')


class UniversityRequest(BaseModel):
    uni_name: str


@app.post("/universities")
async def get_states(request: UniversityRequest):
    uni_name = request.uni_name
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

    if data:
        return {
            'status': 200,
            'data': data,
            'message': 'Universities Found'
        }
    else:
        return {
            'status': 404,
            'data': [],
            'message': 'No Universities Found in this Country'
        }
@app.post("/add_uni")
async def add_uni(data:schemas.AddUni):
    if data.university_name.lower() not in [i["name"].lower() for i in uni_data]:
        data_to_add = {"name": data.university_name, "country": data.Country}
        uni_data.append(data_to_add)
        with open('address/universities.json', 'w') as file:
            json.dump(uni_data, file, indent=4)
        return {'status':200,'data':'Successfully Added','message':'Successfully Added'}
    data_res = {'message': 'University is already Present in List',
            'data': "Already Exist"}
    return JSONResponse(
        status_code=409,
        content=data_res
    )


# Get all applications
@app.get("/application/{id}")
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.Application).filter(models.Application.id == id).first()
    if not user:
        data = {'message': "Not Found",
                'data': "Not found"}
        return JSONResponse(
            status_code=404,
            content=data
        )
    return {'status': 200, 'data': user, 'message': 'Success'}

@app.post("/application_get")
async def get_all_applications(query: schemas.ApplicationQuery, db: Session = Depends(get_db)):
    final_result = []

    if query.ids and query.name:
        for id in query.ids:
            for j in statuses:
                if id == j["id"]:
                    final_result.extend(db.query(models.Application).filter(models.Application.status == j["label"],
                                                                            models.Application.student_name.ilike(
                                                                                f"%{query.name}%")).all())

        return {'status': 200, 'data': final_result, 'message': 'Applications fetched successfully by id and name'}
    elif query.ids:
        for id in query.ids:
            for j in statuses:
                if id == j["id"]:
                    final_result.extend(
                        db.query(models.Application).filter(models.Application.status == j["label"]).all())

        return {'status': 200, 'data': final_result, 'message': 'Applications fetched successfully by id'}

    elif query.name:
        agents = db.query(models.Application).filter(models.Application.student_name.ilike(f"%{query.name}%")).all()
        if not agents:
            return {'status': 200, 'data': [], 'message': 'Application not found'}
        else:
            return {'status': 200, 'data': agents, 'message': 'Success by name'}
    else:
        agents = db.query(models.Application).all()

    return {'status': 200, 'data': agents, 'message': 'Success all '}


@app.post("/application")
async def CU_Applications(application: schemas.Application, request: Request, db: Session = Depends(get_db)):
    role_name = await get_role_from_token(request)
    user = db.query(models.User).filter(models.User.id == application.student_id).first()
    if application.university_name not in [i["name"] for i in uni_data]:
        data_to_add = {"name": application.university_name, "country": application.Country}
        uni_data.append(data_to_add)
        with open('address/universities.json', 'w') as file:
            json.dump(uni_data, file, indent=4)

    if user:
        rent_time = datetime.utcnow()
        current_time = rent_time.strftime('%Y-%m-%d %H:%M:%S')
        if application.id and application.id > 0:
            db_application = db.query(models.Application).filter(models.Application.id == application.id).first()
            if db_application:
                # Update existing application
                for key, value in application.dict(exclude_unset=True).items():
                    setattr(db_application, key, value)
                new_log = models.Logs(
                    operation="Created",
                    timestamp=get_time(),
                    details=f"New Application Created for <b>{user.name}</b> by <b>{role_name}</b>")
                db.add(new_log)

                # Set the student_name from the User table
                db_application.student_name = user.name
                db_application.timestamp = current_time
                db.commit()
                db.refresh(db_application)
                db.refresh(new_log)
                return {'status': 200, 'data': db_application, 'message': 'Application details updated'}
            else:
                print("Update Error")
                data = {'message': "Not Found",
                        'data': "Not found"}
                return JSONResponse(
                    status_code=404,
                    content=data
                )
        else:
            # Create new application without an id
            new_application = models.Application(**application.dict(exclude={"id"}))

            new_application.status = "Application Created"
            # Set the student_name from the User table
            new_application.student_name = user.name
            new_application.timestamp = current_time
            db.add(new_application)
            db.commit()
            db.refresh(new_application)

            new_log = models.Logs(
                operation="Created",
                timestamp=get_time(),
                details=f"New Application Created for <b>{user.name}</b> by <b>{role_name}</b>"
            )
            db.add(new_log)
            db.commit()
            db.refresh(new_log)

            return {'status': 200, 'data': 'New Application Created', 'message': 'New application created'}
    else:
        return {'status': 404, 'data': 'No student with given ID', 'message': 'No student with given ID'}


@app.delete("/application_delete/{id}")
async def delete_application(id: int, db: Session = Depends(get_db)):
    Application = db.query(models.Application).filter(models.Application.id == id).first()
    if not Application:
        data = {'message': "Not Found",
                'data': "Not found"}
        return JSONResponse(
            status_code=404,
            content=data
        )
    db.delete(Application)
    db.commit()
    return {'status': 204, 'data': 'Application Deleted', 'message': 'Application Deleted'}


# </----Applications/---->\


# <----Course Search---->

@app.post("/search_courses/")
def search_courses(search: schemas.CourseSearch, db: Session = Depends(get_db)):
    response = []
    conditions = []
    final_query = []
    if search.global_search:
        final_res = []
        pattern = search.global_search.replace(" ", "").lower()
        if search.course_name:
            name_conditions = [models.CourseName.course_name.ilike(f"%{cname}%") for cname in search.course_name]
            conditions.append(or_(*name_conditions))

        if search.university_name:
            uni_conditions = [models.CourseName.uni_name.ilike(f"%{uni}%") for uni in search.university_name]
            conditions.append(or_(*uni_conditions))

        if search.study_permit:
            permit_conditions = [models.CourseName.study_permit == permit for permit in search.study_permit]
            conditions.append(or_(*permit_conditions))

        final_condition = and_(*conditions)

        query = db.query(models.CourseName).filter(final_condition).all()

        response.append(query)
        final_query = [item for row in response for item in row]
        if final_query:
            for i in final_query:
                course_name = i.course_name.replace(" ", "").lower()
                uni_name = i.uni_name.replace(" ", "").lower()

                # Use the sanitized pattern
                if re.search(pattern, course_name, re.IGNORECASE) or re.search(pattern, uni_name, re.IGNORECASE):
                    final_res.append(i)

            return {'status': 200, 'data': final_res, 'message': 'Success  '}
        else:
            query = db.query(models.CourseName).filter(
                models.CourseName.course_name.ilike(f"%{search.global_search}%")).all()
            query2 = db.query(models.CourseName).filter(
                models.CourseName.uni_name.ilike(f"%{search.global_search}%")).all()
            if query:
                return {'status': 200, 'data': query, 'message': 'Success  '}
            if query2:
                return {'status': 200, 'data': query2, 'message': 'Success  '}
            else:
                return {'status': 200, 'data': [], 'message': 'not found'}

    elif search.course_name or search.university_name or search.study_permit:
        if search.course_name:
            name_conditions = [models.CourseName.course_name.ilike(f"%{cname}%") for cname in search.course_name]
            conditions.append(or_(*name_conditions))

        if search.university_name:
            uni_conditions = [models.CourseName.uni_name.ilike(f"%{uni}%") for uni in search.university_name]
            conditions.append(or_(*uni_conditions))

        if search.study_permit:
            permit_conditions = [models.CourseName.study_permit == permit for permit in search.study_permit]
            conditions.append(or_(*permit_conditions))

        final_condition = and_(*conditions)

        query = db.query(models.CourseName).filter(final_condition).all()

        response.append(query)

        return {'status': 200, 'data': [item for row in response for item in row], 'message': 'Success  '}

    else:
        query = db.query(models.CourseName).all()
        return {'status': 200, 'data': query, 'message': 'Success  '}


@app.post("/search_courses")
def search_courses(search: schemas.CourseSearch, db: Session = Depends(get_db)):
    response = []
    conditions = []
    final_query = []
    if search.global_search:
        final_res = []
        pattern = search.global_search.replace(" ", "").lower()
        if search.course_name:
            name_conditions = [models.CourseName.course_name.ilike(f"%{cname}%") for cname in search.course_name]
            conditions.append(or_(*name_conditions))

        if search.university_name:
            uni_conditions = [models.CourseName.uni_name.ilike(f"%{uni}%") for uni in search.university_name]
            conditions.append(or_(*uni_conditions))

        if search.study_permit:
            permit_conditions = [models.CourseName.study_permit == permit for permit in search.study_permit]
            conditions.append(or_(*permit_conditions))

        final_condition = and_(*conditions)

        query = db.query(models.CourseName).filter(final_condition).all()

        response.append(query)
        final_query = [item for row in response for item in row]
        if final_query:
            for i in final_query:
                course_name = i.course_name.replace(" ", "").lower()
                uni_name = i.uni_name.replace(" ", "").lower()

                # Use the sanitized pattern
                if re.search(pattern, course_name, re.IGNORECASE) or re.search(pattern, uni_name, re.IGNORECASE):
                    final_res.append(i)

            return {'status': 200, 'data': final_res, 'message': 'Success  '}
        else:
            query = db.query(models.CourseName).filter(
                models.CourseName.course_name.ilike(f"%{search.global_search}%")).all()
            query2 = db.query(models.CourseName).filter(
                models.CourseName.uni_name.ilike(f"%{search.global_search}%")).all()
            if query:
                return {'status': 200, 'data': query, 'message': 'Success  '}
            if query2:
                return {'status': 200, 'data': query2, 'message': 'Success  '}
            else:
                return {'status': 200, 'data': [], 'message': 'not found'}

    elif search.course_name or search.university_name or search.study_permit:
        if search.course_name:
            name_conditions = [models.CourseName.course_name.ilike(f"%{cname}%") for cname in search.course_name]
            conditions.append(or_(*name_conditions))

        if search.university_name:
            uni_conditions = [models.CourseName.uni_name.ilike(f"%{uni}%") for uni in search.university_name]
            conditions.append(or_(*uni_conditions))

        if search.study_permit:
            permit_conditions = [models.CourseName.study_permit == permit for permit in search.study_permit]
            conditions.append(or_(*permit_conditions))

        final_condition = and_(*conditions)

        query = db.query(models.CourseName).filter(final_condition).all()

        response.append(query)

        return {'status': 200, 'data': [item for row in response for item in row], 'message': 'Success  '}

    else:
        query = db.query(models.CourseName).all()
        return {'status': 200, 'data': query, 'message': 'Success  '}
# Visa Granted
@app.get("/visa/")
async def get_visa_granted(db: Session = Depends(get_db)):
    for i in statuses:
        if i['label'] == "Visa Granted":
            students1 = db.query(models.Application).filter(models.Application.status == i["label"]).order_by(
                desc(models.Application.id)).all()
    return {'status': 200, 'data': students1, 'message': 'Success all '}



@app.get("/get_uni")
async def get_uni_drop(db: Session = Depends(get_db)):
    uni_data = (
        db.query(
            models.CourseName.uni_name,
            func.count(models.CourseName.id).label('course_count')
        )
        .group_by(models.CourseName.uni_name)
        .all()
    )

    # Constructing the response
    agents_list = [
        {"id": i + 1, "name": uni_name, "count": course_count}
        for i, (uni_name, course_count) in enumerate(uni_data)
    ]
    permit_data = (  # uni_data
        db.query(
            models.CourseName.study_permit,
            func.count(models.CourseName.uni_name).label('course_count')
        )
        .group_by(models.CourseName.study_permit)
        .all()
    )
    permit_list = [
        {"id": i + 1, "name": uni_name, "count": course_count}
        for i, (uni_name, course_count) in enumerate(permit_data)
    ]
    uni_nm_data = (  # uni_data
        db.query(
            models.CourseName.course_name,
            func.count(models.CourseName.uni_name).label('course_count')
        )
        .group_by(models.CourseName.course_name)
        .all()
    )
    course_list = [
        {"id": i + 1, "name": uni_name, "count": course_count}
        for i, (uni_name, course_count) in enumerate(uni_nm_data)
    ]
    return {'status': 200, 'data': {"uni_data": agents_list, "permit_data": permit_list, "course_data": course_list},
            'message': 'Success'}

#
# @app.post("/csv")
# async def get_data(student: schemas.AgentWiseStudent, db: Session = Depends(get_db)):
#     agentWiseStudent = []
#     response = []
#     final_result_with_search = []
#     name = student.name
#
#     agent_ids = student.agent_id
#     if student.agent_id:
#         for id in agent_ids:
#             agent_name = db.query(models.agent_data).filter(models.agent_data.id == id).all()
#             agentWiseStudent.append(agent_name[0].name.replace(" ", "").lower())
#             # print(agentWiseStudent)
#
#         # getting students with that agent
#         for agent_name in agentWiseStudent:
#             students = db.query(models.User).all()
#             matched_students = [student for student in students if
#                                 student.agent.replace(" ", "").lower() == agent_name]
#             response.append(matched_students)
#
#     flat_data = [item for sublist in response for item in sublist]
#
#     # Convert the data to a DataFrame
#     df = pd.DataFrame(flat_data)
#
#     # Use BytesIO as an in-memory buffer
#     output = BytesIO()
#
#     # Create a Pandas Excel writer using XlsxWriter as the engine
#     with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
#         df.to_excel(writer, sheet_name='Agent_name', index=False)
#
#     # Ensure the buffer is set to the beginning of the stream
#     output.seek(0)
#
#     # Send the response with the correct headers
#     return Response(
#         content=output.read(),
#         media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#         headers={"Content-Disposition": "attachment; filename=Madhavoverseas_Data.xlsx"}
#     )
#     # df = pd.DataFrame({'Data': [10, 20, 30, 20, 15, 30, 45]})
#     #
#     # # Use BytesIO as an in-memory buffer
#     # output = BytesIO()
#     #
#     # # Create a Pandas Excel writer using XlsxWriter as the engine
#     # with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
#     #     df.to_excel(writer, sheet_name='Agent_name')
#     #
#     # # Ensure the buffer is set to the beginning of the stream
#     # output.seek(0)
#     #
#     # # Send the response with the correct headers
#     # return Response(
#     #     content=output.read(),
#     #     media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#     #     headers={"Content-Disposition": "attachment; filename=Madhavoverseaas_Data.xlsx"}
#     # )
def model_to_dict(model):
    """
    Convert SQLAlchemy model instance to a dictionary.
    """
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}


@app.post("/csv")
async def get_data(student: schemas.AgentWiseStudent, db: Session = Depends(get_db)):
    agent_ids = student.agent_id
    response = []
    agentWiseStudent = []
    output = BytesIO()
    agent_length=db.query(
            func.count(models.agent_data.id)
        ).all()
    ag_length=agent_length[0][0]
    # Create a Pandas Excel writer using XlsxWriter as the engine
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    if agent_ids:
        if len(agent_ids) ==ag_length:
        #     with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        #         for id in agent_ids:
        #             agent_name = db.query(models.agent_data).filter(models.agent_data.id == id).first()
        #             agentWiseStudent.append(agent_name.name.replace(" ", "").lower())
        #
        #             # getting students with that agent
        #             # for agent_name in agentWiseStudent:
        #             students = db.query(
        #                 models.User.name,
        #                 models.User.email,
        #                 models.User.phone,
        #                 models.User.agent,
        #                 models.User.address,
        #                 models.User.city,
        #                 models.User.state,
        #                 models.User.country,
        #                 models.User.passport
        #             ).all()
        #             matched_students = [student for student in students if
        #                                 student.agent.replace(" ", "").lower() == agent_name]
        #             response.extend(matched_students)  # Use extend instead of append to flatten the list
        #
        #         # Convert each row object to a dictionary
        #     flat_data = [student._asdict() for student in response]
        #
        #         # Convert the data to a DataFrame
        #     df = pd.DataFrame(flat_data)
        #     df.index += 1
        #
        #     df.to_excel(writer, index=True)
        #
        #     # Ensure the buffer is set to the beginning of the stream
        #     output.seek(0)
        #
        # # Send the response with the correct headers
        #     return Response(
        #         content=output.read(),
        #         media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        #         headers={"Content-Disposition": "attachment; filename=Madhavoverseas_Data.xlsx"}
        #     )
        # else:
            for id in agent_ids:
                # Get agent name
                agent_name = db.query(models.agent_data).filter(models.agent_data.id == id).first()
                sheet_name = agent_name.name.replace(" ", "").lower()
                # print(agent_name.name)
                # Query the students related to this agent
                students = db.query(
                    models.User.name,
                    models.User.email,
                    models.User.phone,
                    models.User.agent,
                    models.User.address,
                    models.User.city,
                    models.User.state,
                    models.User.country,
                    models.User.passport
                ).all()

                # Filter students by agent name
                matched_students = [
                    student for student in students if student.agent.replace(" ", "").lower() == sheet_name
                ]
                if  matched_students:
                # Convert the data to a list of dictionaries
                    flat_data = [student._asdict() for student in matched_students]

                    # Create a DataFrame for this agent's students
                    df = pd.DataFrame(flat_data)
                    df.index += 1

                    # Write the DataFrame to a new sheet
                    df.to_excel(writer, sheet_name=sheet_name,index_label="Sr no.")


        writer.close()

        # Ensure the buffer is set to the beginning of the stream
        output.seek(0)

        # Send the response with the correct headers
        return Response(
            content=output.read(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=Madhavoverseas_Data.xlsx"}
        )
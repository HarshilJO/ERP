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
# import xlswriter
from datetime import datetime, timedelta
import pandas as pd
import requests
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

async def currency_convert(curr, amount):
    # created by Harshil on 1-09
    url = "https://api.exchangerate-api.com/v4/latest/"
    response = requests.get(url + f"{curr}")
    res = response.json()
    indian_val = res["rates"].get("INR", None)
    ind_val = float(indian_val)
    amount = float(amount)

    final_val = amount * ind_val
    return final_val

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
async def app_status_update(
    app_status: schemas.application_status, db: Session = Depends(get_db)
):
   
    db_user = (
        db.query(models.Application)
        .filter(models.Application.id == app_status.id)
        .first()
    )
    # print(name[0].student_name)
    if app_status.name == "Visa Granted":
        app_data = []
        app_data.append(db_user)

        db_agent = (
            db.query(models.User.agent)
            .filter(models.User.id == app_data[0].student_id)
            .first()
        )
        app_data.append(db_agent)
        appli = app_data[0].id
        student = app_data[0].student_name
        currency = app_data[0].curr
        agents = app_data[1].agent
        db_agent_id = (
            db.query(models.agent_data.id)
            .filter(models.agent_data.name == agents)
            .first()
        )
        db_agent_commission = (
            db.query(models.agent_data.commission)
            .filter(models.agent_data.id == db_agent_id.id)
            .first()
        )
        app_data.append(db_agent_id)
        app_data.append(db_agent_commission)


        agent_id = app_data[2].id
        curr = app_data[0].curr
        yearly_fee = app_data[0].yearly_fee
        scholarship = float(app_data[0].scholarship)
        scholarship2 =scholarship / 100
        fee_paying = str(round(float((float(yearly_fee) * scholarship2)))) if scholarship > 0 else str(yearly_fee)


        #  1000 - (1000 * 50.85/100)
        charges = "0"
        tds = "5"
        gst = "0"
        rate = "0"
        gain_commission = app_data[3].commission
        after_com = float(fee_paying) - (float(gain_commission) / 100) * float(
            fee_paying
        )

        final_amount = after_com

        db_commission = models.commission(
            application_id=appli,
            Student_name=student,
            agent_id=agent_id,
            agent=agents,
            currency=curr,
            yearly_fee=yearly_fee,
            scholarship=scholarship,
            pay_fee=fee_paying,
            charges=charges,
            tds=tds,
            gst=gst,
            rate = rate,
            gain_commission=gain_commission,
            final_amount=final_amount,
            pay_recieve=0,
        )
        db.add(db_commission)
        db_user.status = app_status.name
        db.commit()
        db.refresh(db_commission)
        db.refresh(db_user)
        return {
            "response": 200,
            "data": "Application Status Updated",
            "message": "Application Status Updated",
        }
    else:
        current_data = []
        current_data.append(db_user)

        db_agent = (
            db.query(models.commission)
            .filter(models.commission.application_id == current_data[0].id)
            .first()
        )
        if db_agent:
            db.delete(db_agent)

    db_user.status = app_status.name
    db.commit()
    db.refresh(db_user)
    return {
        "response": 200,
        "data": "Application Status Updated",
        "message": "Application Status Updated",
    }



def create_access_token(data: dict):
    try:
        to_encode = data.copy()
        SECRET_KEY = "09d25e094faa****************f7099f6f0f4caa6cf63b88e8d3e7"

        # encryption algorithm
        ALGORITHM = "HS256"
        # expire time of the token - set to 100 years
        expire = datetime.utcnow() + timedelta(days=365*100)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        # return the generated token
        return encoded_jwt
    except Exception as e:
        logger.error("Error creating access token: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Login route
@app.post("/login")
def login(user: schemas.Credentials, db: Session = Depends(get_db)):
    try:
        db_user = db.query(models.Credentials).filter(models.Credentials.email == user.email).first()
        if db_user:
            if db_user.password == user.password:
                position = 'Admin' if db_user.is_admin else 'Employee'
                data = {
                    'Role': position,
                    'email': user.email
                }
                token = create_access_token(data=data)
                content = {'message': "Login Successful",
                           'data': {"role": position, "email": user.email, "token": token}}

                response = JSONResponse(
                    status_code=200,
                    content=content
                )
                response.headers["Authorization"] = f"Bearer {token}"
                return response

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
    except Exception as e:
        logger.error("Error during login: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# </----Login----/>


# <----Dashboard----->
@app.get("/Dashboard/")
async def Dashboard(db: Session = Depends(get_db)):
    logger.info("Dashboard endpoint called.")
    
    # Fetch timestamps from the Application model
    try:
        timestamps = db.query(models.Application.timestamp).all()
        timestamps = [t[0] for t in timestamps]
        logger.info(f"Fetched {len(timestamps)} timestamps.")
    except Exception as e:
        logger.error(f"Error fetching timestamps: {e}")
        return {'status': 500, 'message': 'Error fetching timestamps'}

    # Process timestamps to extract month info
    try:
        df = pd.DataFrame(timestamps, columns=['timestamp'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['month'] = df['timestamp'].dt.month
        month_counts = df['month'].value_counts().sort_index()
        logger.info("Processed timestamps into month_counts.")
    except Exception as e:
        logger.error(f"Error processing timestamps: {e}")
        return {'status': 500, 'message': 'Error processing timestamps'}

    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
        7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    month_counts.index = month_counts.index.map(month_names)
    radialBar = [{"label": month, "series": count} for month, count in month_counts.items()]
    logger.info(f"RadialBar data prepared: {radialBar}")

    # Fetch agent data and prepare donut chart
    try:
        result = db.query(models.User.agent, func.count(models.User.id)).group_by(models.User.agent).all()
        donut = [{"label": agent, "series": count} for agent, count in result]
        logger.info(f"Donut chart data prepared: {donut}")
    except Exception as e:
        logger.error(f"Error fetching donut data: {e}")
        return {'status': 500, 'message': 'Error fetching donut data'}

    # Fetch additional counts
    try:
        Student_data = db.query(models.User).order_by(desc(models.User.id)).limit(6).all()
        count_student = db.query(models.User).count()
        count_application = db.query(models.Application).count()
        count_agent = db.query(models.agent_data).count()
        count_pending_application = db.query(models.Application).filter(models.Application.status != "Application Completed").count()
        count_done_application = db.query(models.Application).filter(models.Application.status == "Application Completed").count()
        total_visa_granted = db.query(models.Application).filter(models.Application.status == "Visa Granted").count()
        
        logger.info("Fetched all required counts.")
    except Exception as e:
        logger.error(f"Error fetching counts: {e}")
        return {'status': 500, 'message': 'Error fetching counts'}

    total_count = {
        "student_count": count_student,
        "Application_count": count_application,
        "Agent_count": count_agent,
        "Application_Completed": count_done_application,
        "Application_Incomplete": count_pending_application,
        "RadialBar": radialBar,
        "donut": donut,
        "data": Student_data,
        "visa": total_visa_granted
    }

    logger.info(f"Final response data: {total_count}")
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
    logger.info(f"Fetching application with id {id}")
    try:
        user = db.query(models.Application).filter(models.Application.id == id).first()

        if not user:
            logger.warning(f"Application with id {id} not found")
            data = {'message': "Not Found", 'data': "Not found"}
            return JSONResponse(status_code=404, content=data)

        logger.info(f"Application with id {id} fetched successfully")
        return {'status': 200, 'data': user, 'message': 'Success'}
    except Exception as e:
        logger.error(f"Error fetching application with id {id}: {e}")
        logger.error(traceback.format_exc())  # Logs the full stack trace
        return JSONResponse(status_code=500, content={'message': 'Internal Server Error'})


@app.post("/application_get")
async def get_all_applications(query: schemas.ApplicationQuery, db: Session = Depends(get_db)):
    try:
        filters = []
 
        # Filter by agent_id
        if query.agent_id:
            agent_names = [agent.name for agent_id in query.agent_id for agent in db.query(models.agent_data).filter(models.agent_data.id == agent_id).all()]
            student_ids = [student.id for agent in agent_names for student in db.query(models.User).filter(models.User.agent == agent).all()]
            application_student_ids = [app.student_id for app in db.query(models.Application.student_id).all()]
            common_student_ids = set(student_ids).intersection(application_student_ids)
            filters.append(models.Application.student_id.in_(common_student_ids))
 
        # Filter by status IDs if provided
        if query.ids:
            status_labels = []
            for id in query.ids:
 
                status_labels.append(statuses[id-1]["label"])
            print(status_labels)
            if status_labels:
                filters.append(models.Application.status.in_(status_labels))
 
        # Filter by name if provided
        if query.name:
            filters.append(models.Application.student_name.ilike(f"%{query.name}%"))
 
        # Apply filters to the query
        query_result = db.query(models.Application).filter(*filters).all()
 
        if query_result:
            return {'status': 200, 'data': query_result, 'message': 'Applications fetched successfully'}
        else:
            return {'status': 200, 'data': [], 'message': "No applications found"}
 
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        logger.error(traceback.format_exc())  # Logs the full stack trace
        return JSONResponse(status_code=500, content={'message': 'Internal Server Error'})

@app.post("/application")
async def CU_Applications(application: schemas.Application, request: Request, db: Session = Depends(get_db)):
    try:
        role_name = await get_role_from_token(request)
        logger.info(f"Role {role_name} is attempting to create or update an application")

        user = db.query(models.User).filter(models.User.id == application.student_id).first()
        if not user:
            logger.warning(f"No user found with student_id {application.student_id}")
            return {'status': 404, 'data': 'No student with given ID', 'message': 'No student with given ID'}

        if application.university_name not in [i["name"] for i in uni_data]:
            logger.info(f"Adding new university to uni_data: {application.university_name}")
            data_to_add = {"name": application.university_name, "country": application.Country}
            uni_data.append(data_to_add)
            with open('address/universities.json', 'w') as file:
                json.dump(uni_data, file, indent=4)

        rent_time = datetime.utcnow()
        current_time = rent_time.strftime('%Y-%m-%d %H:%M:%S')

        if application.id and application.id > 0:
            logger.info(f"Updating application with id {application.id}")
            db_application = db.query(models.Application).filter(models.Application.id == application.id).first()

            if db_application:
                for key, value in application.dict(exclude_unset=True).items():
                    setattr(db_application, key, value)

                new_log = models.Logs(
                    operation="Updated",
                    timestamp=get_time(),
                    details=f"Application updated for <b>{user.name}</b> by <b>{role_name}</b>"
                )
                db.add(new_log)
                db_application.student_name = user.name
                db_application.timestamp = current_time
                db.commit()
                db.refresh(db_application)
                db.refresh(new_log)

                logger.info(f"Application {application.id} updated successfully")
                return {'status': 200, 'data': db_application, 'message': 'Application details updated'}
            else:
                logger.error(f"Application with id {application.id} not found for update")
                data = {'message': "Not Found", 'data': "Not found"}
                return JSONResponse(status_code=404, content=data)

        else:
            logger.info("Creating new application")
            new_application = models.Application(**application.dict(exclude={"id"}))
            new_application.status = "Application Created"
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

            logger.info("New application created successfully")
            return {'status': 200, 'data': 'New Application Created', 'message': 'New application created'}
    except Exception as e:
        logger.error(f"Error in creating/updating application: {e}")
        logger.error(traceback.format_exc())  # Logs the full stack trace
        return JSONResponse(status_code=500, content={'message': 'Internal Server Error'})


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


@app.post("/csv")
async def get_data(student: schemas.AgentWiseStudent, db: Session = Depends(get_db)):
    try:
        agent_ids = student.agent_id
        app_id=student.application_id
        output = BytesIO()
        logging.info(f"Agent IDs received: {agent_ids}")
        

        # Create a Pandas Excel writer using XlsxWriter as the engine
        writer = pd.ExcelWriter(output, engine='openpyxl')

        if agent_ids:
            for id in agent_ids:
                agent_name = db.query(models.agent_data).filter(models.agent_data.id == id).first()
                logging.info(f"Processing agent: {agent_name.name if agent_name else 'Not found'}")

                if not agent_name:
                    logging.warning(f"Agent ID {id} not found in the database.")
                    continue

                sheet_name = agent_name.name.replace(" ", "").lower()
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
                ).filter(models.User.agent.ilike(f'%{agent_name.name}%')).all()

                logging.info(f"Number of students found for agent {sheet_name}: {len(students)}")

                if students:
                    flat_data = [student._asdict() for student in students]
                    df = pd.DataFrame(flat_data)
                    df.index += 1
                    df.to_excel(writer, sheet_name=sheet_name, index_label="Sr no.")

            
            writer.close()

            output.seek(0)
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=Madhavoverseas_Data.xlsx"}
            )
        elif app_id:
            app_list=[]

            for id in app_id:
                agent_name = db.query(models.Application).filter(models.Application.id == id).first()
                logging.info(f"Processing agent: {agent_name.student_name if agent_name else 'Not found'}")
                

                if not agent_name:
                    logging.warning(f"Agent ID {id} not found in the database.")
                    continue

                # sheet_name = agent_name..replace(" ", "").lower()
                students = db.query(
                    models.Application.student_name,
                    models.Application.Country,
                    models.Application.university_name,
                    models.Application.intake,
                    models.Application.program_level,
                    models.Application.program,
                    models.Application.status,
                    models.Application.yearly_fee,
                    models.Application.scholarship,
                    models.User.agent
                    
                ).filter(models.Application.id == id,models.Application.student_id==models.User.id).order_by(models.User.agent).first()
                app_list.append(students)
                # print(app_list)

                # logging.info(f"Number of students found for agent {sheet_name}: {len(students)}")

                # if students:
                #     flat_data = [student._asdict() for student in students]
                #     df = pd.DataFrame(flat_data)
                #     df.index += 1
                #     df.to_excel(writer, index_label="Sr no.")

            print(app_list)
            if students:
                    flat_data = [student._asdict() for student in app_list]
                    df = pd.DataFrame(flat_data)
                    df.index += 1
                    df.to_excel(writer, index_label="Sr no.")
            writer.close()

            output.seek(0)
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=Madhavoverseas_Data.xlsx"}
            )
        else:
            logging.error("No agent IDs provided.")
            raise HTTPException(status_code=400, detail="No agent IDs provided.")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Visa Granted
@app.get("/visa/")
async def get_visa_granted(db: Session = Depends(get_db)):
    for i in statuses:
        if i["label"] == "Visa Granted":
            students1 = (
                db.query(models.Application)
                .filter(models.Application.status == i["label"])
                .order_by(desc(models.Application.id))
                .all()
            )
    return {"status": 200, "data": students1, "message": "Success all "}
    


@app.get("/get_uni")
async def get_uni_drop(db: Session = Depends(get_db)):
    uni_data = (
        db.query(
            models.CourseName.uni_name,
            func.count(models.CourseName.id).label("course_count"),
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
            func.count(models.CourseName.uni_name).label("course_count"),
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
            func.count(models.CourseName.uni_name).label("course_count"),
        )
        .group_by(models.CourseName.course_name)
        .all()
    )
    course_list = [
        {"id": i + 1, "name": uni_name, "count": course_count}
        for i, (uni_name, course_count) in enumerate(uni_nm_data)
    ]
    return {
        "status": 200,
        "data": {
            "uni_data": agents_list,
            "permit_data": permit_list,
            "course_data": course_list,
        },
        "message": "Success",
    }


# @app.post("/csv")
# async def get_data(student: schemas.AgentWiseStudent, db: Session = Depends(get_db)):
#     try:
#         agent_ids = student.agent_id
#         output = BytesIO()
#         logging.info(f"Agent IDs received: {agent_ids}")

#         # Create a Pandas Excel writer using XlsxWriter as the engine
#         writer = pd.ExcelWriter(output, engine="openpyxl")

#         if agent_ids:
#             for id in agent_ids:
#                 agent_name = (
#                     db.query(models.agent_data)
#                     .filter(models.agent_data.id == id)
#                     .first()
#                 )
#                 logging.info(
#                     f"Processing agent: {agent_name.name if agent_name else 'Not found'}"
#                 )

#                 if not agent_name:
#                     logging.warning(f"Agent ID {id} not found in the database.")
#                     continue

#                 sheet_name = agent_name.name.replace(" ", "").lower()
#                 students = (
#                     db.query(
#                         models.User.name,
#                         models.User.email,
#                         models.User.phone,
#                         models.User.agent,
#                         models.User.address,
#                         models.User.city,
#                         models.User.state,
#                         models.User.country,
#                         models.User.passport,
#                     )
#                     .filter(models.User.agent.ilike(f"%{agent_name.name}%"))
#                     .all()
#                 )

#                 logging.info(
#                     f"Number of students found for agent {sheet_name}: {len(students)}"
#                 )

#                 if students:
#                     flat_data = [student._asdict() for student in students]
#                     df = pd.DataFrame(flat_data)
#                     df.index += 1
#                     df.to_excel(writer, sheet_name=sheet_name, index_label="Sr no.")

#             writer.close()

#             output.seek(0)
#             return StreamingResponse(
#                 output,
#                 media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                 headers={
#                     "Content-Disposition": "attachment; filename=Madhavoverseas_Data.xlsx"
#                 },
#             )
#         else:
#             logging.error("No agent IDs provided.")
#             raise HTTPException(status_code=400, detail="No agent IDs provided.")
#     except Exception as e:
#         logging.error(f"An error occurred: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")



@app.post("/select_commission")
async def get_comm(
    commission: schemas.select_commission, db: Session = Depends(get_db)
):

    if commission.data:
        total_amount = 0
        total_profit = 0
        total_recieved = 0
        total_pending = 0
        # Collect all ids to query them in a single batch
        ids = [each_data["id"] for each_data in commission.data]
        db_rows = (
            db.query(models.commission).filter(models.commission.id.in_(ids)).all()
        )

        # Create a dictionary to map ids to rows for quick lookup
        db_row_dict = {row.id: row for row in db_rows}

        for each_data in commission.data:
            db_row = db_row_dict.get(each_data["id"])
            if db_row is None:
                continue  # Skip if the row doesn't exist

            final_amount = db_row.final_amount
            amount = db_row.pay_fee
            currency = db_row.currency
            current_rate = db_row.rate
            com = db_row.gain_commission

            if commission.action:

                gst = each_data["gst"]
                current_rate = each_data["rate"]
                tds = each_data["tds"]
                com = each_data["commission"]
                charge = each_data["charges"]

                db_row.charges = charge
                db_row.gain_commission = com
                db_row.tds = tds
                db_row.gst = gst
                db_row.rate = current_rate

            isPaid = db_row.pay_recieve
            

            if isPaid:
                total_recieved += float(final_amount)
                com = float(com)

                total_profit += float((float(com / 100)) * final_amount)
                
                total_amount += final_amount

            else:
                # Change the currency to INR
                if commission.action:
                    current_rate = float(current_rate) if current_rate else 1
                    amount = round(float(amount))

                    tds = float(tds)
                    gst = float(gst)
                    com = float(com)
                    charge = float(charge)
                    if tds < 0 or gst < 0 or com < 0 or charge < 0:
                        data = {"message": "Incorrect input", "data": "invalid"}
                        return JSONResponse(status_code=403, content=data)

                    # print(amount)
                    com_amount = amount * (com / 100)
                    
                    
                    after_charge = (
                        (com_amount - charge) * current_rate
                        if charge > 0
                        else com_amount * current_rate
                    )
                    
                    after_tds = (
                        ((tds / 100) * after_charge) if tds > 0 else after_charge
                    )
                    
                    
                    after_gst = after_tds - ((gst / 100) * after_tds) if gst > 0 else 0
                    
                    final_amount = after_charge - after_tds - after_gst if after_tds != after_charge else after_charge - after_gst
                    
                    # total_profit += (com / 100) * after_charge if com > 0 else 0
                    db_row.final_amount = round(float(final_amount), 3)
                total_amount += final_amount
                total_pending += final_amount
            db.commit()  # Commit once after all updates
            db.refresh(db_row)  # Refresh once after all updates

        return {
            "status": 200,
            "data": {
                "total": round(total_amount, 3),
                "profit": round(total_profit, 3),
                "pending": round(total_pending, 3),
                "recieved": round(total_recieved, 3),
            },
            "message": "success",
        }

    else:
        db_commissions = db.query(models.commission).all()
        return {"status": 200, "data": db_commissions, "message": "Success"}




@app.post("/change_fee_status")
async def get_comm(pay_data: schemas.change_status_fee, db: Session = Depends(get_db)):
    stored_password = "2621"

    db_commissions = (
        db.query(models.commission).filter(models.commission.id == pay_data.id).first()
    )
    if db_commissions.pay_recieve == 0:
        if pay_data.password == stored_password:
            db_commissions.pay_recieve = 1
        else:
            data = {"message": "Incorrect password!", "data": "Unauthorized"}
            return JSONResponse(status_code=401, content=data)
        db_commissions.pay_recieve = 1
        db.commit()
        db.refresh(db_commissions)
        return {"status": 200, "data": "Success", "message": "Success"}
    else:
        data = {"message": "already paid", "data": "already paid"}
        return JSONResponse(status_code=409, content=data)


@app.post("/commission_get")
async def get_comm(commission: schemas.commission_get, db: Session = Depends(get_db)):
    app_data = []

    # Selected agent
    if commission.agent_ids:
        response2 = []
        for agent in commission.agent_ids:
            db_commissions = (
                db.query(models.commission)
                .filter(models.commission.agent_id == agent)
                .all()
            )
            response2.append(db_commissions)
        response2 = [data for row in response2 for data in row]
        return {"status": 200, "data": response2, "message": "Success"}

    # Checking the filter
    if commission.paid_status == 0 or commission.paid_status == 1:
        if commission.paid_status == 1:
            db_commissions = (
                db.query(models.commission)
                .filter(models.commission.pay_recieve == 1)
                .all()
            )
            return {"status": 200, "data": db_commissions, "message": "Success"}
        else:
            db_commissions = (
                db.query(models.commission)
                .filter(models.commission.pay_recieve == 0)
                .all()
            )
            return {"status": 200, "data": db_commissions, "message": "Success"}

    # if filter is not selected
    else:

        db_commissions = db.query(models.commission).all()
        app_data.append(db_commissions)
        return {"status": 200, "data": db_commissions, "message": "Success"}


# @app.post("/expense")
# async def post_expense(
#     expenses: schemas.expense, request: Request, db: Session = Depends(get_db)
# ):
#     role_name = await get_role_from_token(request)
    
    
#     db_expense = models.Expense(
#         description=expenses.description,
#         category=expenses.category,
#         category_id = expenses.category_id,
#         sub_category_id  = expenses.sub_category_id,
#         sub_category=expenses.sub_category,
#         cost=expenses.cost,
#         log_by=role_name,
#         date=expenses.date,
#         expendature=expenses.expendature,
#     )
#     db.add(db_expense)
#     db.commit()
#     db.refresh(db_expense)

#     return {
#         "status": 200,
#         "data": "Success",
#         "message": "Transaction added successfully!",
#     }

@app.post("/expense")
async def post_expense(
    expenses: schemas.expense, request: Request, db: Session = Depends(get_db)
):
    # Fetch role name from token
    role_name = await get_role_from_token(request)
    
    # Fetch category name from database
    db_category_name = db.query(models.Category.category_name).filter(models.Category.id == expenses.category_id).first()
    if db_category_name:
        category_name = db_category_name[0]  # Extract the category name
    else:
        category_name = None

    # Fetch sub-category name from database
    db_category_sub = db.query(models.CategorySub.sub_category_name).filter(models.CategorySub.id == expenses.sub_category_id).first()
    if db_category_sub:
        sub_category_name = db_category_sub[0]  # Extract the sub-category name
    else:
        sub_category_name = None

    # Create Expense model instance
    db_expense = models.Expense(
        description=expenses.description,
        category=category_name,
        category_id=expenses.category_id,
        sub_category_id=expenses.sub_category_id,
        sub_category=sub_category_name,
        cost=expenses.cost,
        log_by=role_name,
        date=expenses.date,
        expendature=expenses.expendature,
    )
    
    # Add, commit, and refresh the Expense instance
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    return {
        "status": 200,
        "data": "Success",
        "message": "Transaction added successfully!",
    }

@app.get("/get_category")
async def getCategory(id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    
    db_category = db.query(models.Category).all()
    db_sub = db.query(models.CategorySub).filter(models.CategorySub.category_id == id).all()
    return {'status':200,'data':{'category':db_category,'sub_category':db_sub},'message':'success'}

@app.post("/get_expense")
async def get_expense(fil: schemas.getExpenses, db: Session = Depends(get_db)):


    # card values
    netTotal = 0.0
    income_ = 0.0
    expense_ = 0.0
    db_income = db.query(models.Expense.cost).filter(models.Expense.expendature == 1).all()
    db_expense = db.query(models.Expense.cost).filter(models.Expense.expendature == 0).all()
    if db_income:
            income = [round(float(item[0]),3) for item in db_income]
            for cost in income:
                income_+=cost
                netTotal+=cost
    if db_expense:
            expense = [round(float(item[0]),3) for item in db_expense]
            for cost in expense:
                netTotal-=cost
                expense_+=cost

    if fil.search or fil.category_ids or fil.sub_category_ids or fil.status==1 or fil.status ==0 :
        
        common_ids = []
        status_ids = []
        if fil.status == 0 or fil.status == 1:
            db_query = db.query(models.Expense.id).filter(models.Expense.expendature == fil.status).all()
            status_ids.append(db_query)
            
            flatten = [item for row in status_ids for item in row]
            status_ids = [item[0] for item in flatten]
            
            
        if fil.category_ids:
            
            ids = fil.category_ids
            # getting ids in category
            for id in ids:
                db_query = db.query(models.Expense.id).filter(models.Expense.category_id == id).all()
                common_ids.append(db_query)
            flatten = [item for row in common_ids for item in row]
            common_ids = [item[0] for item in flatten]
            common_ids = list(set(common_ids))

        if fil.sub_category_ids:
            sub  = []
            sub_ids =  fil.sub_category_ids
            # getting ids in sub_category
            for id in sub_ids:
                db_query =  db.query(models.Expense.id).filter(models.Expense.sub_category_id == id).all()
                sub.append(db_query)
            flatten = [item for row in sub for item in row]
            sub = [item[0] for item in flatten]
            sub = list(set(sub))
            
           
            
            if common_ids:
               
                common_ids= list(set(common_ids).intersection(set(sub)))
            else:
                common_ids = common_ids+sub
                
                            
                

        if fil.search:
            pattern = fil.search.lower().replace(" ","")    
            if not common_ids and not status_ids :
                    
                    db_search = db.query(models.Expense).filter(
                    func.trim(models.Expense.category).ilike(f"%{pattern}%")
                    | func.trim(models.Expense.sub_category).ilike(f"%{pattern}%")
                    | func.trim(models.Expense.description).ilike(f"%{pattern}%")
                ).all()
                    return {'status':200,'data':{'total':netTotal,'income':income_,'expense':expense_,'content':db_search},'message':'Success with only search'} 
             
            else:
                res = []
                searchWithCategory = []    
                if common_ids and status_ids:
                    
                    final_ids= list(set(common_ids).intersection(set(status_ids)))
                    for id in final_ids:
                        db_query = (
                            db.query(models.Expense).filter(models.Expense.id == id).first()
                        )
                        if db_query:
                            res.append(db_query)
                    
                    for row in res:
                        desc = row.description.lower().replace(" ","")
                        category  = row.category.lower().replace(" ","")
                        sub = row.sub_category.lower().replace(" ","")
                        if re.search(pattern, desc, re.IGNORECASE) or re.search(
                                pattern, category, re.IGNORECASE
                            ) or re.search(pattern,sub,re.IGNORECASE):
                            searchWithCategory.append(row)

                    return {'status':200,'data':{'total':netTotal,'income':income_,'expense':expense_,'content':searchWithCategory},'message':'success3'}
                
                if common_ids:
                    
                    for id in common_ids:
                        db_query = db.query(models.Expense).filter(models.Expense.id == id).first()
                        res.append(db_query)

                    for row in res:
                        desc = row.description.lower().replace(" ","")
                        category  = row.category.lower().replace(" ","")
                        sub = row.sub_category.lower().replace(" ","")
                        if re.search(pattern, desc, re.IGNORECASE) or re.search(
                                pattern, category, re.IGNORECASE
                            ) or re.search(pattern,sub,re.IGNORECASE):
                            searchWithCategory.append(row)

                    return {'status':200,'data':{'total':netTotal,'income':income_,'expense':expense_,'content':searchWithCategory},'message':'success'}
                
                if status_ids:
                    
                    
                    for id in status_ids:
                        db_query = db.query(models.Expense).filter(models.Expense.id == id).first()
                        res.append(db_query)
                    for row in res:
                        desc = row.description.lower().replace(" ","")
                        category  = row.category.lower().replace(" ","")
                        sub = row.sub_category.lower().replace(" ","")
                        if re.search(pattern, desc, re.IGNORECASE) or re.search(
                                pattern, category, re.IGNORECASE
                            ) or re.search(pattern,sub,re.IGNORECASE):
                            searchWithCategory.append(row)

                    return {'status':200,'data':{'total':netTotal,'income':income_,'expense':expense_,'content':searchWithCategory},'message':'success'}

        if common_ids or status_ids:
            
            res = []
                
            inco = 0.0        
            exp = 0.0
            total = 0.0
    
    
            common_ids = list(set(common_ids))
            
            if common_ids and status_ids:
                
                final_ids= list(set(common_ids).intersection(set(status_ids)))
                
                for id in final_ids:
                    db_query = (
                        db.query(models.Expense).filter(models.Expense.id == id).first()
                    )
                    
                    if db_query:
                        if db_query.expendature:
                            inco+=round(float(db_query.cost),3)
                            total+=round(float(db_query.cost),3)
                        else:
                            exp+=round(float(db_query.cost),3)
                            total-=round(float(db_query.cost),3)
                        res.append(db_query)
                return {'status':200,'data':{'total':total,'income':inco,'expense':exp,'content':res},'message':'success'}

            if common_ids:
                print("3")
                for id in common_ids:
                    
                    db_query = (
                        db.query(models.Expense).filter(models.Expense.id == id).first()
                    )
                    if db_query:
                        res.append(db_query)
                        if db_query.expendature:
                            inco+=round(float(db_query.cost),3)
                            total+=round(float(db_query.cost),3)
                        else:
                            exp+=round(float(db_query.cost),3)
                            total-=round(float(db_query.cost),3)
                return {'status':200,'data':{'total':total,'income':inco,'expense':exp,'content':res},'message':'success'}
            
            if status_ids:
                
                db_query = (
                    db.query(models.Expense).filter(models.Expense.expendature == fil.status).all()
                )
                 
                return {'status':200,'data':{'total':netTotal,'income':income_,'expense':expense_,'content':db_query},'message':'success'}
        else:
            return {'status':200,'data':{'total':0.0,'income':0.0,'expense':0.0,'content':[]},'message':'success'}
                
    else:
    
        db_expenses = db.query(models.Expense).all()
        return {"status": 200, "data": {'total':netTotal,'income':income_,'expense':expense_,'content':db_expenses}, "message": "success"}




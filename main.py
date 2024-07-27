from fastapi import FastAPI, Depends, HTTPException, status, Request, Query
from app import models, schemas
from app.database import engine, SessionLocal
from sqlalchemy.orm import Session
import re
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List,Optional
import json
from fastapi.middleware.cors import CORSMiddleware
import logging

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

#<----Validations---->
NAME_REGEX = re.compile(r"^[a-zA-Z_]+(?: [a-zA-Z_]+)*$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PASSWORD_REGEX = re.compile(r"^(?=.[A-Za-z])(?=.\d)[A-Za-z\d]{8,}$")
PHONE_REGEX = re.compile(r"^[6-9][0-9]{9}$")
#</----Validations----/>

#<----Login---->
@app.post("/login")
def login(user: schemas.Credentials,db: Session = Depends(get_db)):
    db_user = db.query(models.Credentials).filter(models.Credentials.email == user.email).first()
    if db_user:
        if db_user.password == user.password:
            return {'status': 200, 'message': 'User found','data': json.loads(json.dumps(({"Role":db_user.is_admin, "token":db_user.token})))}
        else:
            return {'status': 200, 'message': 'Incorrect Password'}
    else:
        
        return {'status': 200, 'message': 'Not found'}
#</----Login----/>

# Admin authentication
@app.get("/admin/{id}")
async def get_admin(id: int, db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.id == id).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin Not Found")
    return {'status': 200, 'data': admin, 'message': 'Success'}

#<----Student Detils---->
@app.get("/users/")
async def read_users(name: Optional[str] = Query(None),db: Session = Depends(get_db)):
    if name:
        user_data = db.query(models.User).filter(models.User.name.ilike(f"%{name}%")).all()
        
        if not user_data:
            raise HTTPException(status_code=404, detail="Agent not found")
    else:
        user_data = db.query(models.User).all()
    return {'status': 200, 'data': user_data, 'message': 'Success'}

# User creation or update endpoint
@app.post("/users/")
async def create_or_update_user(user: schemas.User, db: Session = Depends(get_db)):
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
            for key, value in user.dict(exclude_unset=True).items():
                setattr(db_user, key, value)
            db.commit()
            db.refresh(db_user) 
            return {'status': 200, 'data': db_user, 'message': 'Success'}
    
    # Create new user
    db_user = models.User(**user.dict(exclude={"id"}))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {'status': 200,  'message': 'Success'}




@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"detail": "User deleted"}
#</----Student Details----/>
# Get all applications
@app.get("/applications")
async def get_all_applications(db: Session = Depends(get_db)):
    applications = db.query(models.Application).all()
    return applications

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

# Agent Details
@app.get("/agent")
async def get_all_agent(name: Optional[str] = Query(None),db: Session = Depends(get_db)):

    if name:
        agents = db.query(models.agent_data).filter(models.agent_data.name.ilike(f"%{name}%")).all()
        
        if not agents:
            raise HTTPException(status_code=404, detail="Agent not found")
    else:
        agents = db.query(models.agent_data).all()
    return {'status': 200, 'data': agents, 'message': 'Success'}

    # all_agent = db.query(models.agent_data).all()
    # return {'status': 200, 'data': all_agent, 'message': 'Success'}

@app.get("/agent/{id}", response_model=schemas.AgentSchema)

async def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.agent_data).filter(models.agent_data.id == id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_user
@app.post("/agents/")
async def CU_agent(agent: schemas.AgentSchema, db: Session = Depends(get_db)):
    if agent.id and agent.id > 0:
        db_agent = db.query(models.agent_data).filter(models.agent_data.id == agent.id).first()
        if db_agent:
            # Update existing agent
            for key, value in agent.dict(exclude_unset=True).items():
                setattr(db_agent, key, value)
            db.commit()
            db.refresh(db_agent)
            return {'status': 200,'data':db_agent ,'message': 'Agent Details Updated'}
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
    else:
        # Create new agent without an id
        new_agent = models.agent_data(**agent.dict(exclude={"id"}))
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        return {'status': 200,'data':new_agent , 'message': 'New Agent Created'}

@app.delete("/agent_delete/{id}")
async def delete_agent(id: int, db: Session = Depends(get_db)):
    user = db.query(models.agent_data).filter(models.agent_data.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent Not Found")
    db.delete(user)
    db.commit()
    return {'status': 204, 'message': 'Agent Deleted'}
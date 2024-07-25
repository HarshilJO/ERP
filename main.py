from fastapi import FastAPI, Depends, HTTPException, status
from app import models, schemas
from app.database import engine, SessionLocal
from sqlalchemy.orm import Session
import re
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import json
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust this as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
#TO run this code:
#Use~~ uvicorn main:app --host 26.243.124.232 --port 8080 --reload
#use for normal loading: uvicorn main:app  --reload &&& http://127.0.0.1:8000/docs#/default/
#To See the output use this link : http://26.243.124.232:8080/docs#/
# Create database tables



# Create database tables
models.Base.metadata.create_all(engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Admin authentication
@app.get("/admin/{id}")
async def get_admin(id: int, db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.id == id).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin Not Found")
    return {'status': 200, 'data': admin, 'message': 'Success'}

# Create user
@app.post("/user_create")
def CU_user(agent: schemas.User, db: Session = Depends(get_db)):
    if agent.id and agent.id > 0:
        db_agent = db.query(models.User).filter(models.User.id == agent.id).first()
        if db_agent:
            # Update existing agent
            for key, value in agent.dict(exclude_unset=True).items():
                setattr(db_agent, key, value)
            
            db.commit()
            db.refresh(db_agent)
            return {'status': 200, 'message': 'User Details Upated'}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        # Create new agent without an id
        new_agent = models.agent_data(**agent.dict(exclude={"id"}))
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        return {'status': 200, 'message': 'New User Created'}
   

# Update user details
# @app.put("/user_update/{id}")
# async def update_user(id: int, request: schemas.User, db: Session = Depends(get_db)):
#     user = db.query(models.User).filter(models.User.id == id).first()
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
#     for attr, value in request.dict(exclude_unset=True).items():
#         setattr(user, attr, value)
#     db.commit()
#     db.refresh(user)
#     return {'status': 200, 'message': 'User Updated'}

# Get all users
@app.get("/users")
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return {'status': 200, 'data': users, 'message': 'Success'}

# Get user by id
@app.get("/user/{id}")
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
    return {'status': 200, 'data': user, 'message': 'Success'}

# Delete user
@app.delete("/user_delete/{id}")
async def delete_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
    db.delete(user)
    db.commit()
    return {'status': 204, 'message': 'User Deleted'}

# Get all applications
@app.get("/applications")
async def get_all_applications(db: Session = Depends(get_db)):
    applications = db.query(models.Application).all()
    return applications
#<----Address Details-->
# Load data from a JSON file
def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)
# Load the JSON data
data = load_json('address/countries.json')
class Country(BaseModel):
    id: int
    name: str

class State(BaseModel):
    id: int
    name: str

class City(BaseModel):
    id: int
    name: str

@app.get("/countries")
def get_countries():
    return {'status': 200, 'data': [{"id": country["id"], "name": country["name"]} for country in data], 'message': 'Success'}
@app.get("/countries/{country_id}/states")
def get_states(country_id: int):
    for country in data:
        if country["id"] == country_id:
            if "states" in country:
                return {'status': 200, 'data': [{"id": state["id"], "name": state["name"]} for state in country["states"]], 'message': 'Success'}
            else:
                return {'status': 404, 'data': [], 'message': 'No states found for this country'}
    raise HTTPException(status_code=404, detail="Country not found")
@app.get("/states/{state_id}/cities")
def get_cities(state_id: int):
    for country in data:
        if "states" in country:
            for state in country["states"]:
                if state["id"] == state_id:
                    if "cities" in state:
                        return {'status': 200, 'data': [{"id": city["id"], "name": city["name"]} for city in state["cities"]], 'message': 'Success'}
                    else:
                        return {'status': 404, 'data': [], 'message': 'No cities found for this state'}
    raise HTTPException(status_code=404, detail="State not found")
#</----end of Address Details----/>

#<----Docs Dropdown---->
@app.post("/options/", response_model=schemas.DropdownOptionOut)
def create_option(option: schemas.DropdownOptionCreate, db: Session = Depends(get_db)):
    db_option = models.DocsDropdown(name=option.name)
    db.add(db_option)
    db.commit()
    db.refresh(db_option)
    return db_option

@app.get("/options/", response_model=List[schemas.DropdownOptionOut])
def read_options(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    options = db.query(models.DocsDropdown).offset(skip).limit(limit).all()
    return options
#</----Docs Dropdown----/>

#<----Agent Details---->
@app.get("/agent")
async def get_all_agent(db: Session = Depends(get_db)):
    all_agent = db.query(models.agent_data).all()
    return {'status': 200, 'data':all_agent , 'message': 'Success'}

@app.post("/agents/")
def CU_agent(agent: schemas.AgentSchema, db: Session = Depends(get_db)):
    if agent.id and agent.id > 0:
        db_agent = db.query(models.agent_data).filter(models.agent_data.id == agent.id).first()
        if db_agent:
            # Update existing agent
            for key, value in agent.dict(exclude_unset=True).items():
                setattr(db_agent, key, value)
            
            db.commit()
            db.refresh(db_agent)
            return {'status': 200, 'message': 'Agent Details Upated'}
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
    else:
        # Create new agent without an id
        new_agent = models.agent_data(**agent.dict(exclude={"id"}))
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        return {'status': 200, 'message': 'New Agent Created'}
    
@app.delete("/agent_delete/{id}")
async def delete_agent(id: int, db: Session = Depends(get_db)):
    user = db.query(models.agent_data).filter(models.agent_data.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent Not Found")
    db.delete(user)
    db.commit()
    return {'status': 204, 'message': 'Agent Deleted'}

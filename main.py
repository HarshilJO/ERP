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

#<----Student details---->
# Create user
# @app.post("/user_create")
# def CU_user(agent: schemas.User, db: Session = Depends(get_db)):
#     if agent.id and agent.id > 0:
#         db_agent = db.query(models.User).filter(models.User.id == agent.id).first()
#         if db_agent:
#             # Update existing agent
#             for key, value in agent.dict(exclude_unset=True).items():
#                 setattr(db_agent, key, value)
            
#             db.commit()
#             db.refresh(db_agent)
#             return {'status': 200, 'message': 'User Details Upated'}
#         else:
#             raise HTTPException(status_code=404, detail="User not found")
#     else:
#         # Create new agent without an id
#         new_agent = models.agent_data(**agent.dict(exclude={"id"}))
#         db.add(new_agent)
#         db.commit()
#         db.refresh(new_agent)
#         return {'status': 200, 'message': 'New User Created'}
# # Get all users
# @app.get("/users")
# async def get_all_users(db: Session = Depends(get_db)):
#     users = db.query(models.User).all()
#     return {'status': 200, 'data': users, 'message': 'Success'}
# # Get user by id
# @app.get("/user/{id}")
# async def get_user(id: int, db: Session = Depends(get_db)):
#     user = db.query(models.User).filter(models.User.id == id).first()
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
#     return {'status': 200, 'data': user, 'message': 'Success'}
# # Delete user
# @app.delete("/user_delete/{id}")
# async def delete_user(id: int, db: Session = Depends(get_db)):
#     user = db.query(models.User).filter(models.User.id == id).first()
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
#     db.delete(user)
#     db.commit()
#     return {'status': 204, 'message': 'User Deleted'}
#</----Student Details----/>
@app.post("/users/", response_model=schemas.User)
def create_or_update_user(user: schemas.User, db: Session = Depends(get_db)):
    if user.id and user.id > 0:
        db_user = db.query(models.User).filter(models.User.id == user.id).first()
        if db_user:
            # Update existing user
            db_user.name = user.name
            db_user.email = user.email
            db_user.phone = user.phone
            db_user.address = user.address
            db_user.gender = user.gender
            db_user.passport = user.passport
            db_user.pass_Expiry = user.pass_Expiry
            db_user.agent = user.agent
            db_user.single = user.single
            db_user.docs = [item.dict() for item in user.docs]
            db.commit()
            db.refresh(db_user)
            return db_user
    
    # Create new user
    db_user = models.User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        address=user.address,
        gender=user.gender,
        passport=user.passport,
        pass_Expiry=user.pass_Expiry,
        agent=user.agent,
        single=user.single,
        docs=[item.dict() for item in user.docs]
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"detail": "User deleted"}

@app.get("/users/", response_model=List[schemas.User])
def read_users(db: Session = Depends(get_db)):
    db_users = db.query(models.User).all()
    return db_users
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
@app.post("/docs/", response_model=schemas.DropdownOptionOut)
def create_option(option: schemas.DropdownOptionCreate, db: Session = Depends(get_db)):
    db_option = models.DocsDropdown(name=option.name)
    db.add(db_option)
    db.commit()
    db.refresh(db_option)
    return db_option

@app.get("/docs/", response_model=List[schemas.DropdownOptionOut])
def read_options(db: Session = Depends(get_db)):
    options = db.query(models.DocsDropdown).all()
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

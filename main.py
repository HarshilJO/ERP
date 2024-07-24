from fastapi import FastAPI, Depends, HTTPException, status
from app import models, schemas
from app.database import engine, SessionLocal
from sqlalchemy.orm import Session
import re
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import json
app = FastAPI()
#TO run this code:
#Use~~ uvicorn main:app --host 26.243.124.232 --port 8080 --reload 
#To See the output use this link : http://26.243.124.232:8080/docs#/default/
# Create database tables
models.Base.metadata.create_all(engine)
# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# admin authentication
@app.get("/admin/{id}")
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.admin).filter(models.admin.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user Not Found")
    return {'status':200,'data':user,'message':'Success'}
# Create user
@app.post("/user_create")
async def create_user(request: schemas.user, db: Session = Depends(get_db)):
    new_user = models.user(**request.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {'status': 200, 'message': 'user Created'}

# Update user details
@app.put("/user_update/{id}")
async def update_user(id: int, request: schemas.user, db: Session = Depends(get_db)):
    user = db.query(models.user).filter(models.user.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user Not Found")
    for attr, value in request.dict(exclude_unset=True).items():
        setattr(user, attr, value)
    db.commit()
    db.refresh(user)
    return {'status': 200, 'message': 'user Updated'}

# Get all users
@app.get("/users")
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.user).all()
    return {'status':200,'data':users,'message':'Success'}

# Get user by id
@app.get("/user/{id}")
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.user).filter(models.user.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user Not Found")
    return {'status':200,'data':user,'message':'Success'}

# Delete user
@app.delete("/user_delete/{id}")
async def delete_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.user).filter(models.user.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user Not Found")
    db.delete(user)
    db.commit()
    return {'status': 204, 'message': 'user Deleted'}

# Get all applications
@app.get("/applications")
async def get_all_applications(db: Session = Depends(get_db)):
    applications = db.query(models.Application).all()
    return applications
# Load data from a JSON file
def load_json(filename):
    with open(filename,'r',encoding='utf-8') as file:
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
@app.get("/countries" )
def get_countries(): 
    return {'status':200,'data':[{"id":country["id"],"name": country["name"]} for country in data],'message':'Success'}
   
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
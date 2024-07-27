from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app import models, schemas
from app.database import engine, SessionLocal
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
import re
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import json
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime, timedelta

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

# Secret key for JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Create database tables
models.Base.metadata.create_all(engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db, email: str):
    return db.query(models.Credentials).filter(models.Credentials.email == email).first()

def authenticate_user(db, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, email=email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

#<----Login---->
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

#<----Secured Endpoints---->
@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(get_current_active_user)):
    return current_user

@app.get("/users/")
async def read_users(name: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):
    if name:
        user_data = db.query(models.User).filter(models.User.name.ilike(f"%{name}%")).all()
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        user_data = db.query(models.User).all()
    return {'status': 200, 'data': user_data, 'message': 'Success'}

# User creation or update endpoint
@app.post("/users/")
async def create_or_update_user(user: schemas.User, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):
    phone_str = str(user.phone)
    # Validate phone number as a string
    a = re.fullmatch(r'[6-9][0-9]{9}', phone_str)
    if not NAME_REGEX.match(user.name):
        return {'status': 400, 'message': 'Invalid Name'}
    if not EMAIL_REGEX.match(user.email):
        return {'status': 400, 'message': 'Invalid Email'}
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
    return {'status': 200, 'message': 'Success'}

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"detail": "User deleted"}

# Get all applications
@app.get("/applications")
async def get_all_applications(db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):
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
async def create_option(option: schemas.DropdownOptionCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):
    db_option = models.DocsDropdown(name=option.name)
    db.add(db_option)
    db.commit()
    db.refresh(db_option)
    return db_option

@app.get("/docs/")
async def read_options(db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):
    options = db.query(models.DocsDropdown).all()
    return {'status': 200, 'data': options, 'message': 'Success'}

# Agent Details
@app.get("/agent")
async def get_all_agent(name: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):

    if name:
        agents = db.query(models.agent_data).filter(models.agent_data.name.ilike(f"%{name}%")).all()
        if not agents:
            raise HTTPException(status_code=404, detail="Agent not found")
    else:
        agents = db.query(models.agent_data).all()
    return {'status': 200, 'data': agents, 'message': 'Success'}

@app.get("/agent/{id}", response_model=schemas.AgentSchema)
async def read_user(user_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):
    db_user = db.query(models.agent_data).filter(models.agent_data.id == id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_user

@app.post("/agents/")
async def CU_agent(agent: schemas.AgentSchema, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):
    if agent.id and agent.id > 0:
        db_agent = db.query(models.agent_data).filter(models.agent_data.id == agent.id).first()
        if db_agent:
            # Update existing agent
            for key, value in agent.dict(exclude_unset=True).items():
                setattr(db_agent, key, value)
            db.commit()
            db.refresh(db_agent)
            return {'status': 200, 'data': db_agent, 'message': 'Agent Details Updated'}
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
    else:
        # Create new agent without an id
        new_agent = models.agent_data(**agent.dict(exclude={"id"}))
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        return {'status': 200, 'data': new_agent, 'message': 'New Agent Created'}

@app.delete("/agent_delete/{id}")
async def delete_agent(id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):
    user = db.query(models.agent_data).filter(models.agent_data.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent Not Found")
    db.delete(user)
    db.commit()
    return {'status': 204, 'message': 'Agent Deleted'}

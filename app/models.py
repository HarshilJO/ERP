from sqlalchemy import Column, Integer, String, ForeignKey,JSON,Boolean,VARCHAR
from app.database import Base

from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    phone = Column(Integer)
    address = Column(String)
    city=Column(String)
    state=Column(String)   
    country=Column(String) 
    gender = Column(String)
    passport = Column(String)
    pass_Expiry = Column(String)
    agent = Column(String)
    single = Column(String)
    docs = Column(JSON)
    logged_by=Column(String)
    applications = relationship("Application", back_populates="user")

class Admin(Base):
    __tablename__ = 'admin'
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String)
    email = Column(String)
    pass_word = Column(String)

class Application(Base):
    __tablename__ = 'application'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('users.id'))
    student_name = Column(String)
    university_name = Column(String)
    intake = Column(VARCHAR)
    program = Column(String)
    user = relationship("User", back_populates="applications")

class DocsDropdown(Base):
    __tablename__ = "docs_dropdown"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)


class agent_data(Base):
    __tablename__= 'agents'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String)
    name = Column(String)
    company_name = Column(String)
    agency_type = Column(String)
    city = Column(String)
    owner_name = Column(String)
    owner_contact = Column(String)
    state = Column(String)
    tel_phone = Column(String)
    address = Column(String)
    con_per_name = Column(String)
    con_per_phone = Column(String)
    con_per_pos =Column(Integer)

class Credentials(Base):
    __tablename__ = 'credentials'
    id = Column(Integer, primary_key=True, index=True)
    is_admin = Column(Boolean)
    email = Column(String)
    password = Column(String)
    token = Column(String)
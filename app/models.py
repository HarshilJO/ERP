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
    state_id=Column(Integer)
    state = Column(String)
    country=Column(String)
    country_id= Column(Integer)
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
    Country=Column(String)
    university_name = Column(String)
    intake = Column(VARCHAR)
    program_level=Column(String)
    program = Column(String)
    status = Column(String)
    timestamp=Column(String)
    curr=Column(String)
    yearly_fee=Column(String)
    scholarship=Column(String)
    user = relationship("User", back_populates="applications")
    # commission=relationship("commission",back_populates="application")

class commission(Base):
    __tablename__="commission"
    id=Column(Integer,primary_key=True,index=True)
    Student_name=Column(String)
    application_id=Column(Integer,ForeignKey('application.id'))
    agent_id=Column(Integer)
    agent=Column(String)
    currency=Column(String)
    yearly_fee=Column(String)
    scholarship=Column(String)
    pay_fee=Column(String)
    charges=Column(String)
    tds=Column(String)
    gst=Column(String)
    rate = Column(String)
    gain_commission=Column(String)
    final_amount=Column(Integer)
    pay_recieve=Column(Integer)
    # application = relationship("Application", back_populates="commision")
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
    commission=Column(Integer)

class Credentials(Base):
    __tablename__ = 'credentials'
    id = Column(Integer, primary_key=True, index=True)
    is_admin = Column(Boolean)
    email = Column(String)
    password = Column(String)
    token = Column(String)

class Logs(Base):
    __tablename__ = 'logs'
    id=Column(Integer,primary_key = True,index = True)
    operation = Column(String)
    timestamp = Column(String)
    details = Column(String)

class CourseAcademicEligibility(Base):
    __tablename__ = "course_academic_eligibility"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('course_name.id'))
    academics=Column(String)
    remarks = Column(String)

    # Specify foreign_keys to resolve ambiguity
    course_name = relationship("CourseName", back_populates="academics", foreign_keys=[course_id])


class CourseName(Base):
    __tablename__ = "course_name"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_name = Column(String)
    uni_name = Column(String)  # Changed to Integer for consistency
    academics = relationship("CourseAcademicEligibility", back_populates="course_name",foreign_keys=[CourseAcademicEligibility.course_id])
    fees=Column(String)
    scholarship=Column(String)
    study_permit=Column(Integer)
    ielts = Column(String)
    pte = Column(String)


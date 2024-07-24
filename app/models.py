from sqlalchemy import Column, Integer, String, ForeignKey,DATE
from app.database import Base
from sqlalchemy.orm import relationship


class user(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    phone = Column(Integer)
    address = Column(String)
    gender =Column(String)
    passport =Column(String)
    pass_Expiry=Column(String)
    agent=Column(String)
    single=Column(String)
    user=relationship("application",back_populates="application")

class admin(Base):
    __tablename__='admin'

    id = Column(Integer, primary_key=True, index=True)
    token =Column(String)
    email = Column(String)
    pass_word =Column(String)

class application(Base):
    __tablename__='application'

    id = Column(Integer, primary_key=True, index=True)
    student_id =Column(Integer,ForeignKey(user.id))
    university_name=Column(String)
    intake=Column(String)
    program=Column(String)
    applications=relationship("user",back_populates="user")

# class agent(Base):
#      __tablename__ = 'agents'

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String)
#     email = Column(String)
#     phone = Column(Integer)
#     address = Column(String)
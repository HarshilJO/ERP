from sqlalchemy import Column, Integer, String, Float, DateTime, DECIMAL, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class countries(Base):
    __tablename__ = 'countries+states'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    country_id = Column(Integer, nullable=False)
    country_code = Column(String(2), nullable=False)
    fips_code = Column(String(255))
    iso2 = Column(String(255))
    type = Column(String(191))
    latitude = Column(DECIMAL)
    longitude = Column(DECIMAL)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.current_timestamp())
    flag = Column(Integer, nullable=False, default=1)
    wikiDataId = Column(String(255))

    def __repr__(self):
        return f"<City(name='{self.name}', country_id={self.country_id}, country_code='{self.country_code}')>"

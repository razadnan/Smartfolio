from sqlalchemy import Column, Integer, String
from database import Base

class Promotion(Base):
    __tablename__ = "promotions"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)
    champion_version = Column(String)
    challenger_version = Column(String)
    decision = Column(String)
    reason = Column(String)

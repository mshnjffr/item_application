"""
SQLAlchemy model representing an item in the database.

Attributes:
    id (int): Primary key for the item
    name (str): Name of the item, indexed for faster queries
    description (str): Description of the item
    price (int): Price of the item
    quantity (int): Available quantity of the item
"""
from sqlalchemy import Column, Integer, String
from database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Integer)
    quantity = Column(Integer)

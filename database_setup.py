""" This module defines the database for the catalog project """

import random
import string
import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

DATABASE = declarative_base()
SECRET_KEY = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))


class User(DATABASE):
    """ This class defines the attributes of a user """
    __tablename__ = 'users'
    ident = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    picture = Column(String)
    email = Column(String)


class Category(DATABASE):
    """ This class defines the attributes of a catagory """
    __tablename__ = 'categories'
    ident = Column(Integer, primary_key=True)
    name = Column(String(50))

    @property
    def serialize(self):
        """ Serialize the category object """
        return {
            'id' : self.ident,
            'name' : self.name
        }


class Item(DATABASE):
    """ This class defines the attributes of an item """
    __tablename__ = 'items'
    ident = Column(Integer, primary_key=True)
    name = Column(String(50))
    date_added = Column(String(8))
    desc = Column(String)
    owner_ident = Column(Integer, ForeignKey('users.ident'))
    user = relationship('User')
    category_ident = Column(Integer, ForeignKey('categories.ident'))
    category = relationship('Category')

    @property
    def serialize(self):
        """ Serialize the Item object """
        return {
            'cat_id' : self.category_ident,
            'description' : self.desc,
            'id' : self.ident,
            'title' : self.name
        }

    @staticmethod
    def create_time(mapper, connection, instance):
        """ Before insert triggered code from SQLAlchemy event listener """
        now = datetime.datetime.now()
        instance.date_added = now.strftime("%Y-%m-%d")

    @classmethod
    def register(cls):
        """ Register SQLAlchemy event listener(s) """
        event.listen(cls, 'before_insert', cls.create_time)


ENGINE = create_engine('sqlite:///catalog.db')

DATABASE.metadata.create_all(ENGINE)

Item.register()

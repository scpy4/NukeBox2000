from sqlalchemy import create_engine

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import ForeignKey

from sqlalchemy.orm import Query
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref

from sqlalchemy.ext.declarative import declarative_base


engine = create_engine('mysql://root:root@localhost/nukebox')

# create a configured "Session" class
Session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.metadata.bind = engine

# turns Session.query(User) into User.query
Base.query = Session.query_property(Query)

# Initialize database schema (create tables)
Base.metadata.create_all(engine)


# Class Mapped to Users Table
class Users(Base):

    '''
    B{Users Table Object}
    '''

    __tablename__ = 'users'

    user_id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(20))
    mac_id = Column(String(30))

    files = relationship(
        'Files', backref='users', cascade='all, delete-orphan'
    )


# Class Mapped to Files table
class Files(Base):

    '''
    B{Files Table Object}
    '''

    __tablename__ = 'files'

    file_id = Column(Integer, autoincrement=True, primary_key=True)
    path = Column(String(255))
    size = Column(Integer)
    filetype = Column(String(10))
    title = Column(String(30))
    artist = Column(String(30))
    genre = Column(String(30))
    album = Column(String(30))
    duration = Column(String(10))

    user_id = Column(Integer, ForeignKey('users.user_id'))


# Mgmt Class, used to Get-or-Create objects
class NukeBoxMgr(object):

    '''
    B{Nukebox Manager Class}

      - Class to Contain Static Method "Get or Create"
    '''

    @staticmethod
    def get_or_create(session, model, **filters):

        '''
        Get or Create an DB Object given the **kwargs received
        '''

        # Try to Retrieve an Existing obj
        try:
            obj = session.query(model).filter_by(**filters).one()
            print('Exists!')
            return True, obj

        # Except when None Exists, then Create it
        except:
            print('Does not Exist!')
            obj = model(**filters)
            return False, obj


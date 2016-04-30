#! /usr/bin/env python

# import os

# Import the Base Models and Classes
from models import Users, Files, NukeBoxMgr, Base

# SQLAlchemy Imports
from sqlalchemy import create_engine

# ORM Imports
from sqlalchemy.orm import Query
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

# Create the DB Engine
engine = create_engine('mysql+mysqldb://root:root@localhost/nukebox')

# For testing purposes, comment original engine & uncomment below to run in "in memory" db
# engine = create_engine('sqlite://')

# Create a configured "Session" class
Session = scoped_session(sessionmaker(bind=engine))

# Bind the Engine
Base.metadata.bind = engine

# For Convenience - turns Session.query(User) into User.query
Base.query = Session.query_property(Query)

# Initialize database schema (create tables)
Base.metadata.create_all(engine)

# Create a Session
session = Session()


class NukeBoxQuery(object):

    """
    B{NukeBox 2000 Database Query Class}

      - NukeBox 2000 Database Access Object
      - Provides CRUD Methods to manipulate the NukeBox DB
    """

    def __init__(self):

        '''
        NukeBox 2000 Constructor Method

        Constructs a Instance Dictionary used to match a string to a
        Class Model
        '''

        # Models Dict
        self.tables = {'Users': Users,
                       'Files': Files
                       }

    def __enter__(self):

        '''
        Simply returns the instance
        '''
        return self

    def __exit__(self, exc_type, exc_value, traceback):

        '''
        Clean Up
        '''
        print('Cleaning Up DB Instance')
        pass

    # Create Method
    def create(self, details):

        '''
        Allows NukeBox create new entries in the db for all Tables

          - Takes a Dictionary of Details as an argument.
          - Checks which Table to target.
          - Returns a Row Object.

        B{Syntax}

          - Create Method Syntax

          >>> nbq = NukeBoxQuery()
          >>> result = nbq.create(**kwargs)

          - Alternative Syntax

          >>> with NukeBoxQuery() as nbq:
          >>> ...    result = nbq.create(**kwargs)

          - Expects a Dictionary of Key: Value Arguments.

          Note: must specify the Table ('Model') to target, for example:

          >>> {'Model': 'Files',
               'path': '/home/music/what_went_down.mp3',
               'size': 10000,
               'filetype': 'mp3',
               'title': 'WHAT WENT DOWN',
               'artist': 'Foals',
               'genre': 'Indie',
               'album': 'WHAT WENT DOWN',
               'duration': '5:00', 'user_id': 2}

          - Returns a Row Object ('result')
          - Access Values with result.attribute

          >>> print(result.user_id, result.name, result.mac_id)
        '''

        # Pull the Model that we want to work with
        model_choice = details['Model']
        model = self.tables[model_choice]

        # Delete the Model entry from the dict, may interfere!
        del details['Model']

        # If the Target Model is Users
        if model_choice == 'Users':

            # Call on Get/Create and pass in keyword values
            exists, user_obj = NukeBoxMgr.get_or_create(
                session,
                model,
                **details
            )

            print(exists)

            # If it didn't already exist, add & commit
            if not exists:
                session.add(user_obj)
                session.commit()

            user = Users.query.filter(
                getattr(Users, 'mac_id') == user_obj.mac_id).one()

            return user

        # If the Target Model is Files
        elif model_choice == 'Files':

            # Call on Get/Create and pass in keyword values
            exists, file_obj = NukeBoxMgr.get_or_create(
                session,
                model,
                **details
            )

            print(exists)

            # If it didn't already exist, add & commit
            if not exists:
                session.add(file_obj)
                session.commit()

            # Use the PK to get the object
            file_o = Files.query.get(file_obj.file_id)

            # Return the object
            return file_o

    # Read Method
    def read(self, **details):

        """
        Reads can only be performed using unique entries in the DB.

          - Files can only be filtered on its 'path' & 'title' attributes.
          - Users can only be filtered on its 'mac_id' attribute.
          - Returns a Row Object.

        The program has access to the path & title variables which can
        uniquely identify rows in the Files Table. It can use the mac_id
        variable to do the same for the Users Table.
        No other values can be used because they would not be unique &
        queries might result in multiple matches e.g. artists, duration
        etc. As such reading may raise Exceptions.

        B{Syntax}

            - Read Method Syntax

            >>> result = nbq.read(**kwargs)

            - Alternative Syntax

            >>> with NukeBoxQuery() as nbq:
            >>> ...    result = nbq.read(**kwargs)

            - Expects a Dictionary of Key: Value Arguments.
              - Use 'mac_id' attribute to identify Users.
              - Use 'path' or 'title' to identify Files.

            Note: must specify the Table ('Model') to target, for example

            >>> {'Model': 'Users',
                 'mac_id': '0987654321'}

            - Returns a Row Object ('result')
            - Access Values with result.attribute

            >>> print(result.user_id, result.name, result.mac_id)
        """

        # Pull the Model that we want to work with
        model_choice = details['Model']
        model = self.tables[model_choice]

        # Delete the Model entry from the dict, may interfere!
        del details['Model']

        # Query using the details
        q = session.query(model).filter_by(**details).one()

        # Return the result
        return q

    # Update Method
    def update(self, **details):

        """
        Updates can only be performed using unique entries in the DB

          - Files can only be filtered on its 'path' & 'title' attributes
          - Users can only be filtered on its 'mac_id' attribute
          - Returns Boolean Value

        The program has access to the path & title variables which can
        uniquely identify rows in the Files Table. It can use the mac_id
        variable to do the same for the Users Table.

        No other values can be used because they would not be unique &
        queries might result in multiple matches e.g. artists, duration
        etc. As such updating could corupt the data.

        B{Syntax}

          - Update Method Syntax

          >>> nbq.read(**kwargs)

          - Alternative Syntax

          >>> with NukeBoxQuery() as nbq:
          >>> ...    result = nbq.update(**kwargs)

          - Expects a Dictionary of Key: Value Arguments
          - Use 'mac_id' attribute to identify Users
          - Use 'path' or 'title' to identify Files

          Note: kwargs must specify the Table ('Model') to target,
          the Column ('column') to filter on & the Value ('value') to update
          , for example:

          >>> {'Model': 'Files',
               'column': 'path',
               'value': '/home/nukebox/what_went_down.mp3',
               'path': '/home/music/what_went_down.mp3'}

          - Returns Boolean to Indicate Success / Failure
        """

        # Pull the Model that we want to work with
        model_choice = details['Model']
        model = self.tables[model_choice]

        # Delete the Model entry from the dict, may interfere!
        del details['Model']

        # Pull the Filter Details
        col = details['column']
        val = details['value']
        print('Details: ' + str(col) + ' = ' + str(val))

        # Delete Filter Details
        del details['column']
        del details['value']

        try:
            # Retrieve the object to Update
            q = model.query.filter(
                getattr(model, col) == val).one()

            # If it is a File, use 'path' (or 'title'?) attribute
            if model_choice == 'Files':
                try:
                    q.path = details['path']
                except:
                    q.title = details['title']

                session.commit()
                q = model.query.get(q.file_id)
                return True

            elif model_choice == 'Users':
                q.mac_id = details['mac_id']

                session.commit()
                q = model.query.get(q.user_id)
                return True

        except:
            print('No Match!')
            return False

    # Delete Method
    def delete(self, **details):

        '''
        Deletes can only be performed using unique entries in the DB

          - Files can only be filtered on its 'path' & 'title' attributes
          - Users can only be filtered on its 'mac_id' attribute
          - Returns Boolean Value

        The program has access to the path & title variables which can
        uniquely identify rows in the Files Table. It can use the mac_id
        variable to do the same for the Users Table.

        No other values can be used because they would not be unique &
        queries would result in multiple matches e.g. artists, duration
        etc. As such deleting could remove the wrong data.

        B{Syntax}

          - Delete Method Syntax

          >>> nbq.delete(**kwargs)

          - Alternative Syntax

          >>> with NukeBoxQuery() as nbq:
          >>> ...    result = nbq.delete(**kwargs)

          - Expects a Dictionary of Key: Value Arguments
            - Use 'mac_id' attribute to identify Users
            - Use 'path' or 'title' to identify Files

          Note: must specify the 'Model' to target, the 'column'
          to filter on & the 'value' to delete on, for example:

          >>> {'Model': 'Users',
               'column': 'mac_id',
               'value': '0123456789'}

          - Returns Boolean to Indicate Success / Failure
        '''

        # Pull the Model that we want to work with
        model_choice = details['Model']
        model = self.tables[model_choice]

        # Pull the Filter Details
        col = details['column']
        val = details['value']
        print('Details: ' + str(col) + ' = ' + str(val))

        # Run the Delete Query & perform a Commit
        q = model.query.filter(
            getattr(model, col) == val).delete()
        session.commit()

        # Return value of 1 indicates Success
        if q == 1:
            return True
        else:
            # No match
            return False


#  # Things To Do (maybe)

# Add a "Logged In" entry in the table, could easily update it from
# the main server when the user disconnects.
# It would have to be more of "Last Logged In" come to think of it.
# We don't hold a connection to the client after we receive the file,
# it gets dropped immediately, so it would log in & out in the time it
# takes to transfer the file. Could attach a "Number of Times Logged in"
# entry too, could be handy.


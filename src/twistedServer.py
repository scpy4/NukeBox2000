#!/usr/bin/env python

from twisted.internet import reactor, protocol, defer
from twisted.internet.threads import deferToThread
from twisted.protocols.basic import LineReceiver

import os
import re
import sys
import pickle
import signal
import subprocess
from shutil import move
from mutagen.id3 import ID3
from StringIO import StringIO
from socket import SOL_SOCKET, SO_BROADCAST

from NukeBoxDB import NukeBoxQuery
from NukeBoxQueue import NukeBoxQueue


class NukeBoxProtocol(LineReceiver):

    '''
    B{NukeBox 2000 Protocol Class}

      - Main Nukebox Protocol Object
      - Responsible for:

        - File Transfer
        - DB Access
        - Queuing
        - Error Checking
    '''

    def __init__(self, factory):

        '''
        Protocol Constructor
        '''

        # Create the Instance Variables

        # Create a Reference to the Parent Factory
        self.factory = factory

        # Set the Users State to New
        self.state = 'New'

        # Set the Initial Total File Size & Percent Variables
        self.sizeTotal = 0
        self.oldPercent = 0

        # Set the Intial State of the Buffer & Filename
        self.buffer = None
        self.fname = None

    def connectionMade(self):

        '''
        Called when the Server receives a new connection
        '''

        # Retrieve Info on the Client
        self.peer = self.transport.getPeer()

    def connectionLost(self, reason):

        '''
        Called when the Server loses a connection
        '''

        # If the user exists in the user dictionary, remove the value
        # associated with them
        if self.client in self.factory.clients:
            del self.factory.clients[self.client]
        else:
            'Not in dict'

    def lineReceived(self, data):

        '''
        Directs new user instances to the Register method
        '''

        # If this is a New User, send them to Register
        # May not be needed in the final implementation
        if self.state == 'New':
            self.register(data)

    def register(self, data):

        '''
        Registers New Clients

        - Deconstructs Data
        - Adds User Entry to DB
        - Sets the User Instance State
        - Initiates File Transfer from Client
        '''

        # Pull the Data apart for the contained info
        obj = pickle.loads(data)
        self.sizeTotal = obj["size"]

        self.fname = obj["filename"]
        self.fname = self.fname.split('/')
        self.fname = self.fname[-1]

        self.client = obj["name"]
        self.mac_id = obj['mac_id']

        print('The Filesize Server Side is ' + str(self.sizeTotal))

        print('Received ' + self.client)

        # Create a Dict obj for the new DB User entry
        user_details = {'Model': 'Users',
                        'name': self.client,
                        'mac_id': self.mac_id
                        }

        # Use 'With' so instance is garbage collected
        with NukeBoxQuery() as nbq:
            user = nbq.create(user_details)

        # Store the user object in the Factory Clients dict
        self.factory.clients[self.client] = user

        # Set the User Sate to Registered
        self.state = 'Reg'

        # Notify the Client that we're Ready for Transfer
        self.sendLine('tx')

        # Set the Ingress Mode to Raw & Create a buffer obj
        self.setRawMode()
        self.buffer = StringIO()

    def rawDataReceived(self, data):

        '''
        Receives the Raw File data

        - Outputs Transfer to stdout
        - Writes Data to Temp File
        - Calls Validate and Tests the Result
        - Sends Ack to Client
        '''

        # Write the Ingress Data to the Buffer obj
        self.buffer.write(data)

        # Calculate the Overall Percent of the File Received
        percent = self.buffer.len * 100/self.sizeTotal

        # # Solely for Displaying Progress of File Tx.
        if self.oldPercent != percent:

            # Increase the oldPercent by what has been Received
            self.oldPercent = percent

            # The Next 4 lines are just for the Progress Bar
            # Flush the Displayed Output
            sys.stdout.flush()
            icon = '# ' * (percent / 5)

            # Display the New % Bar
            sys.stdout.write('\r' + icon + str(percent) + ' %')

        # Flush the Output again
        sys.stdout.flush()

        # Allow for a little Over-run on the File Transfer
        if percent >= 100:

            # Create the Path to the Sandboxed Copy of the File
            self.temp_f_name = self.factory.temp + self.fname

            # Open the Temp File & Write the Data from the Buffer
            f = open(self.temp_f_name, 'w+')

            # Writing File from Buffer
            print('Writing File from Buffer')
            f.write(self.buffer.getvalue())
            print('Finished Writing File from Buffer')

            # Close the Buffer obj
            self.buffer.close()

            # Notify the Client when the Full File is Received
            sys.stdout.write('\n')
            self.sendLine('Ack')

            # Validate the File
            d = defer.Deferred()
            result = self.validateFile(self.temp_f_name, d)
            # d.addCallback(self.validateFile)
            d.addCallback(self.queueFile)
            d.addCallbacks(self.moveFile, self.invalidFile)

    def validateFile(self, path, d):

        '''
        File Validation Method

        - Invokes the Queue File or Invalid File methods
        - Temp validation using id3 tags
        '''
        # d = defer.Deferred()

        try:
            audio = ID3(path)
            self.artist = audio['TPE1'].text[0]
            title = audio["TIT2"].text[0]
            title = title.split('/')
            self.title = title[-1]

            print('Artist: ' + self.artist)
            print('Title: ' + self.title)
            print('File Valid, Firing Callback Chain!')
            d.callback(path)

        except Exception as err:
            print('Error is ', err)
            print('Firing Errback Chain!')
            d.errback(err)

    def queueFile(self, path):

        '''
        File Registration

        - Adds File to the Queuing System
        - Adds an Entry to the DB
        - Invokes Move File Method on Success
        - Invokes Invalid method on Failure
        '''

        # Replace any Empty Space or Special Characters in the Song Title
        title = re.sub('[^\w\-_\.]', '-', self.title)
        # title = self.title.replace(' ', '-')
        self.dst = self.factory.dir + title + '.mp3'
        self.temp_f_name

        # If the File does not exist in the Default Directory, Create It
        if not os.path.isfile(self.dst):
            os.system('touch {}'.format(self.dst))

        # Create a String with the Users Mac ID & File Path
        user_path = self.mac_id + ':' + str(self.dst)

        # If this String Does Not Exist in the Queue
        if user_path not in self.factory.q:

            print('Path not already Queued!\n'
                  'Adding ....')

            # Add Path to the Queue System
            self.factory.q.append(user_path)
            print('Added! :) ')

        # Create a Dict obj for the new DB File entry
        details = {'Model': 'Files',
                   'filetype': '.mp3',
                   'artist': self.artist,
                   'path': self.dst,
                   'title': self.title,
                   'user_id': self.factory.clients[self.client].user_id,
                   'size': self.sizeTotal
                   }

        # Use 'With' so the Instance is Garbage Collected
        print('Adding Entry to the DB ....')
        with NukeBoxQuery() as nbq:

            # Create the File DB Entry
            self.file = nbq.create(details)
        print('DB Appended! :) ')

    def moveFile(self, result):

        '''
        Transfers the Temp File to the Default save Directory

        - Ends Callback Chain
        '''

        print('Moving File ....')
        move(self.temp_f_name, self.dst)
        print('File Moved! :) ')
        print('End of Callback Chain! :) ')

    def invalidFile(self, failure):

        '''
        Reports Invalid File

        - Receives a Exception
        - Removes the Temp File if needs be
        - Ends the Errback Chain
        '''

        print('Invalid!')
        # print(str(failure))

        # If the Temp File Exists, Remove it
        try:
            os.remove(self.temp_f_name)
            delattr(self, 'temp_f_name')

        except:
            print('No Temp File to Delete :) ')

        finally:
            # Return the Failure obj
            print('End of Errback Chain! :) ')


class NukeboxFactory(protocol.ServerFactory):

    '''
    B{NukeBox 2000 Factory Object}

      - Nukebox Factory
      - Responsible for:

        - Creating Protocol Instances
          - One for each new connection
    '''

    def __init__(self, q, default_dir, temp_dir):

        '''
        Constructor for the Nukebox Factory object
        '''

        # Build the Instance Variables

        # Queue System
        self.q = q

        # Default Save Location
        self.dir = default_dir

        # Temporary Save Location
        self.temp = temp_dir

        # Currently Registered Clients Dictionary
        # Might Not Need This For Our Purposes !!
        self.clients = {}

        print('********  Server Up!  ********')

    def buildProtocol(self, addr):

        '''
        Builds instances of Nukebox Protocol

          - One for each new client
        '''

        # Build the Protocol Instance
        return NukeBoxProtocol(self)


class NukeBoxBroadcastReceiver(protocol.DatagramProtocol):

    '''
    B{NukeBox 2000 UDP Class}

      - Nukebox UDP Datagram Protocol
      - Responsible for:

        - Listening for broadcast/discover messages
        - Responding to clients
    '''

    def __init__(self, factory):

        '''
        Constructor Method for the UDP Receiver
        '''

        # Create a Reference to the Parent Factory Class
        self.factory = factory

    def startProtocol(self):

        '''
        Sets the underlying socket to receive UDP packets
        '''

        # Set the underlying socket for UDP
        self.transport.socket.setsockopt(SOL_SOCKET,
                                         SO_BROADCAST,
                                         True)

    def datagramReceived(self, data, addr):

        '''
        Called when a UDP discover message is received
        '''

        print 'Datagram received'

        # If We Receive the Correst String, Respond
        if data == 'Hello Jukebox':
            self.transport.write("This is the JukeBox Speaking. I'm Here",
                                 addr)


def main():

    '''
    Main function
    '''

    def playBack():

        '''
        File PlayBack Function

          - Runs in Thread of its own
          - Continues to check the Queue for new entries
          - Calls VLC CLI command to play file
        '''

        print('Playback called!')

        # While the Server is UP
        while True:

            # If there is an Entry in the Queue
            if len(q) > 0:

                # Pull the Entry at Index 0
                user_path = q.popleft()

                # Split the String into a User ID & File Path
                mac_id, path = user_path.split(':')

                print('User {} - Playing {}').format(mac_id, path)

                # If the File Does Exist
                if os.path.isfile(path):

                    print('File Exists')

                    # Create a String to Call CLVC (VLC command line!)
                    file = 'cvlc --play-and-exit {}'.format(path)

                    # Execute the Command in a Sub Process
                    subprocess.call(file, shell=True)

    def cleanUp(signal, frame):

        '''
        Called to Exit somewhat gracefully
        '''

        reactor.stop()
        os._exit(0)

    # Create the Double Ended Queue (Deque)
    q = NukeBoxQueue()

    # Create a Reference to the Users Home Dir
    HOME = os.path.expanduser('~')

    # Create a String for the Default & Temporary Save Locations
    default_dir = HOME + '/Music/NukeBox2000/'
    temp_dir = '/tmp/NukeBox2000/'

    # If Default Location Does not Exist, Create it
    if not os.path.isdir(default_dir):
        os.makedirs(default_dir)

    # If Temporary Location Does not Exist, Create it
    if not os.path.isdir(temp_dir):
        os.makedirs(temp_dir)

    # Create the Factory Instance
    f = NukeboxFactory(q, default_dir, temp_dir)

    # Notify the Reactor to Listen for TCP Connections
    reactor.listenTCP(8008, f)

    # Create a UDP Protocol Instance
    protocol = NukeBoxBroadcastReceiver(f)

    # Notify the Reactor to Listen for UDP Connections
    reactor.listenUDP(9009, protocol)

    # Add the Shutdown Signal Handler
    signal.signal(signal.SIGINT, cleanUp)

    # Defer the Playback Function to its Own Thread
    deferToThread(playBack)

    # Run the Reactor
    reactor.run()


# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()


#!/usr/bin/env python

# Default Queueing
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
from collections import deque
from mutagen.id3 import ID3

from StringIO import StringIO
from socket import SOL_SOCKET, SO_BROADCAST

from NukeBoxDB import NukeBoxQuery


class NukeBoxProtocol(LineReceiver):

    '''
    NukeBox 2000 Protocol Class
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
        Called when a connection is made to the Server
        '''

        # Retrieve Info on the Client
        self.peer = self.transport.getPeer()

    def connectionLost(self, reason):

        '''
        Called when we lose a connection
        '''

        # If the user exists in the user dictionary remove the value
        # associated with them
        print('Connection Lost')
        if self.client in self.factory.clients:
            del self.factory.clients[self.client]
        else:
            'Not in dict'
        # except Exception as e:
        #    print(e)

    def lineReceived(self, data):

        '''
        Directs "New" Instances to the Register Method
        '''

        # If this is a New User, send them to Register
        # May not be needed in the final implementation
        if self.state == 'New':
            self.register(data)
        # self.setRawMode()

    def register(self, data):

        '''
        Registers New Clients
        - Deconstructs Data
        - Adds Entry to DB
        - Sets the Instance State
        - Initiates File Transfer from Client
        '''

        # Pull the Data apart for the contained info
        obj = pickle.loads(data)
        self.sizeTotal = obj["size"]
        self.fname = obj["filename"]
        self.client = obj["name"]
        self.mac_id = obj['mac_id']

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

        # Asynchronous Operation !
        # While we don't have the Full File
        if self.oldPercent != percent:

            # Increase the oldPercent by what has been Received
            self.oldPercent = percent

        #     # The Next 4 lines are just for the Progress Bar
        #     # Flush the Displayed Output
        #     sys.stdout.flush()
        #     icon = '# ' * (percent / 5)

        #     # Display the New % Bar
        #     sys.stdout.write('\r' + icon + str(percent) + ' %')

        # # Flush the Output again
        # sys.stdout.flush()

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

        # Validate the File
        d = defer.Deferred()
        d.addCallback(self.validateFile)
        d.addCallbacks(self.queueFile, self.invalidFile)

        # # Firing Deferred Validation Callback
        # print('Firing Validation Deferred')
        # d.callback(self.temp_f_name)
        # print('Finished Firing Deferred Validation Callback')

        # Display the Result from Validation
        # Valid returns the Path ; Invalid returns an Exception obj
        # print('Result is ' + str(result.result))

        # Notify the Client when the Full File is Received
        if percent == 100:
            sys.stdout.write('\n')
            self.sendLine('Ack')
            # Firing Deferred Validation Callback
            print('Firing Validation Deferred')
            d.callback(self.temp_f_name)
            print('Finished Firing Deferred Validation Callback')

    # @defer.inlineCallbacks
    def validateFile(self, path):

        '''
        Inline Validation Callback
        - Generator; Yields Values
        - Invokes the Queue File or Invoke File methods
        - Temp using id3 tags
        '''

        try:
            audio = ID3(path)
            self.artist = audio['TPE1'].text[0]
            self.title = audio["TIT2"].text[0]
            print('Artist: ' + self.artist)
            print('Title: ' + self.title)
            print('Valid!')

        except Exception as err:
            print('Error is ', err)
            self.invalidFile(err)

        # finally:
        #     # Remove the file
        #     print('finally here')

        # Have to run proper tests on the file, this is temp
        # defer.returnValue(result)
        # return self

    def queueFile(self, path):

        '''
        File Registration
        - Adds File to the Queuing System
        - Adds an Entry to the DB
        - Returns the Filename as Result
        - Method is part of an Deferred Inline Callback Chain
        -- Success from any "Try" will continue until Returned
        -- Exceptions return control to the Initial Caller ("validate" Method)
        '''

        # Try to Move the Temp File to the NukeBox Directory
        try:

            # Replace any Empty Space or Special Characters in the Song Title
            title = re.sub('[^\w\-_\.]', '-', self.title)
            # title = self.title.replace(' ', '-')
            self.dst = self.factory.dir + title + '.mp3'
            self.temp_f_name

            # If the File does not exist, create it
            if not os.path.isfile(self.dst):
                os.system('touch {}'.format(self.dst))

            # Move the Temp File
            d = defer.Deferred()
            d.addCallback(self.moveFile)
            print('Adding Callback')
            result = 'This is the result'  # required param ?
            d.callback(result)
            print('Out of Call')
            # print('Moving File ' + dst)
            # d = self.moveFile(self.temp_f_name, dst)

            # print('Firing Move File Deferred')
            # d.addCallback(move)
            # print('Finished Firing Move File Deferred')

        # Except when the File Can't be Moved
        # Exceptions will return control to the caller !
        except Exception as e:
            print('Exception is ', e)
            return self.invalidFile(e)

        # Create a String with the Users Mac ID & File Path
        user_path = self.mac_id + ':' + str(self.dst)

        # If this String Does Not Exist in the Queue
        if user_path not in self.factory.q:

            print('Path not already Queued!')

            # Add Path to the Queue System
            self.factory.q.append(user_path)

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
        with NukeBoxQuery() as nbq:

            # Create the File DB Entry
            self.file = nbq.create(details)

        # Return the File Path
        return self.dst

    def moveFile(self, result):

        '''
        '''

        print('Moving File')
        move(self.temp_f_name, self.dst)
        print('Done')

    def invalidFile(self, failure):

        '''
        Reports Invalid File
        - Receives a Exception
        - Removes the Temp File if needs be
        - Returns the Exception as Result
        '''

        # If the Temp File Exists, Remove it
        try:
            os.remove(self.temp_f_name)
            delattr(self, 'temp_f_name')
        except:
            print('No Temp File to Delete')

        print('Invalid!')

        # Return the Failure obj
        return failure


class NukeboxFactory(protocol.ServerFactory):

    '''
    NukeBox 2000 Factory responsible for creating Protocol Instances
    One for each new connection
    '''

    def __init__(self, q, default_dir, temp_dir):

        '''
        Constructor for Factory object
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
        Builds an instance of the Potocol for each client
        '''

        # Build the Protocol Instance
        return NukeBoxProtocol(self)


class NukeBoxBroadcastReceiver(protocol.DatagramProtocol):

    '''
    NukeBox 2000 UDP Receiver/Responder
    '''

    def __init__(self, factory):

        '''
        Constructor Method for the UDP Receiver
        '''

        # Create a Reference to the Parent Factory Class
        self.factory = factory

    def startProtocol(self):

        '''
        Sets up the listener socket to receive UDP packets
        '''

        # Set the underlying socket for UDP
        self.transport.socket.setsockopt(SOL_SOCKET,
                                         SO_BROADCAST,
                                         True)

    def datagramReceived(self, data, addr):

        '''
        Called when a UDP Discover Message is Received
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
                user_path = q.pop()

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
    q = deque()

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

#!/usr/bin/env python

import os
import getpass
import pickle
# from logger import NukeboxLogger
from uuid import getnode as get_mac
from socket import SOL_SOCKET, SO_BROADCAST

from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver


class NukeBoxClientProtocol(LineReceiver):

    '''
    B{NukeBox 2000 Client Protocol Class}

      - Main Nukebox Client Protocol Object
      - Responsible for:

        - File Transfer
    '''

    def __init__(self, factory, fname):

        '''
        Client Protocol constructor method
        '''

        # Create the Instance Variables

        # Create a Reference to the Parent Factory Class
        self.factory = factory

        # Create the Reference to the File
        self.fname = fname

        # Get the Users Name & Mac ID
        self.name = getpass.getuser()
        self.mac = hex(get_mac())

    def connectionMade(self):

        '''
        Called when a connection is made with the server

          - Determines total file size
          - Pickles & then sends client info to the server
        '''

        # Get the Size of the File
        filesize = os.path.getsize(self.fname)

        print('Filesize ' + str(filesize))

        print('Sending Client ' + self.name)

        # Serialize the Gathered Data & Send it to the Server
        self.sendLine(pickle.dumps({"size": filesize,
                                    "filename": self.fname,
                                    "name": self.name,
                                    'mac_id': self.mac}
                                   ))

    def lineReceived(self, data):

        '''
        Called when a piece of data is received

          - Receives Ack from server
          - Initiates File Transfer
        '''

        # If the Server Responds with a Request for Transfer, oblige
        if data == 'tx':

            # Open the File
            f = open(self.fname, "rb")

            # Read the File Contents and Send them to the Server
            contents = f.read()
            self.sendLine(contents)

            # Close the File
            f.close()

        # Drop the Connection to the Server
        else:
            self.transport.loseConnection()

    def connectionLost(self, reason):

        '''
        Called when the connection is lost
        '''

        print('Connection Lost')


class NukeBoxClientFactory(protocol.ClientFactory):

    '''
    B{NukeBox 2000 Client Factory Class}

      - Nukebox Client Factory Object
      - Responsible for:

        - Building Client protocols
        - Reconnecting to server
        - Disconnection from server
        - Destroying the reactor
    '''

    def __init__(self, fname):

        '''
        NukeBoxClient Factory constructor method
        '''

        # Create the Factory Instance Variables
        # self.logger = log
        self.fname = fname
        self.host = ''

    def buildProtocol(self, addr):

        '''
        Builds instances of Nukebox Client Protocol
        '''

        # Build an Instance of the Client Protocol
        return NukeBoxClientProtocol(self, self.fname)

    def clientConnectionFailed(self, connector, reason):

        '''
        Attempt to Reconnect when Connections Fails
        '''

        # Call the Connect Method on the Transport obj
        connector.connect()

    def clientConnectionLost(self, connector, reason):

        '''
        Lost Connections are Discarded

          - Stops the Reactor Loop
        '''

        # Call Disconnect method on the Transport obj & Stop the reactor
        connector.disconnect()
        reactor.stop()


class NukeBoxClientBroadcastProtocol(protocol.DatagramProtocol):

    '''
    B{NukeBox 2000 UDP Class}

      - Nukebox UDP Datagram Protocol Object
      - Responsible for:

        - Tweaking the underlying socket for UDP
        - Sending a UDP packet to find the server
        - Listening for a response
        - Setting up the TCP Protocol
    '''

    def __init__(self, factory):

        '''
        Client UDP Protocol constructor method
        '''

        # Create a reference to the Parent Factory
        self.factory = factory

    def startProtocol(self):

        '''
        Set the Socket for UDP Broadcast Packets
        '''

        # Set the Underlying Socket to UDP
        self.transport.socket.setsockopt(SOL_SOCKET,
                                         SO_BROADCAST,
                                         True)

        # Push out the UDP Packet
        self.sendDatagram()

    def sendDatagram(self):

        '''
        Transmit the UDP Discover Packet
        '''

        # Write the UDP Packet to the Transport
        self.transport.write('Hello Jukebox',
                             ('255.255.255.255', 9009)
                             )

    def datagramReceived(self, data, (ip, port)):

        '''
        Called when a UDP Response is received

          - Uses the Responders address to make TCP Connection
        '''

        # Pull the Server IP Address from the Response & Make the Connection
        self.factory.host = ip
        reactor.connectTCP(ip, 8008, self.factory)


def main():

    '''
    Main test function
    '''

    # This section is only for logging stuff
    # logger = NukeboxLogger('Client FileTX')

    # Test Files
    # fname = "05 ELECTRICBLOOM.mp3"
    fname = "01 (THE FRENCH OPEN).mp3"
    # fname = "02 CASSIUS.mp3"
    # fname = "03 RED SOCKS PUGIE.mp3"
    # fname = "08 TWO STEPS TWICE.mp3"

    # Invalid File Format
    # fname = "jukebox_client.log"

    filesize = os.path.getsize(fname)
    if filesize == 0:

        print('File has No Content! :( ')
        os._exit(1)

    factory = NukeBoxClientFactory(fname)

    print('*** Client Running ***')

    udp_protocol = NukeBoxClientBroadcastProtocol(factory)
    reactor.listenUDP(0, udp_protocol)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()


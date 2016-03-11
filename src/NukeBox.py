#!/usr/bin/env python

from collections import deque

from twistedServer import NukeBoxBroadcastReceiver, NukeboxFactory

from twisted.internet import reactor

from twisted.internet.threads import deferToThread

import os
import signal
# import time
import subprocess


if __name__ == '__main__':

    def playBack():

        '''
        File PlayBack Function
        - Runs in Thread of its own
        - Continues to check the Queue for new entries
        - Calls VLC CLI command to play file
        - Sleeps for 5 secs if it is empty
        '''

        print('Playback called!')

        # os.setpgrp()

        # While the Server is UP
        while True:

            # time.sleep(5)

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

#!/usr/bin/env python

import collections


class NukeBoxQueue(collections.deque):

    '''
    B{NukeBox 2000 Queue Class}

      - NukeBox Queue Object
      - Subclass of collections.deque
      - Responsible for:

        - Adding/Removing items to/from the Queue
    '''

    def __init__(self):

        '''
        Queue Constructor

          - Calls Super on self
        '''

        super(NukeBoxQueue, self).__init__()

    def popleft(self):

        '''
        Deque Pop Left Method

          - Retrieve & Returns an item
        '''

        file = collections.deque.popleft(self)
        if len(self) is 0:
            print('Queue Now Empty')
        return file

    def append(self, value):

        '''
        Deque Append Method

          - Add an item
          - Returns boolean value
        '''

        print('Inside Deque Module: '
              'Value: {}'.format(value))
        if collections.deque.append(self, value):
            print('Added to Queue')
            return True
        return False
        # print('Queue Length Currently {}'.format(str(len(self))))


if __name__ == '__main__':

    to_q_1 = 'I am an entry'
    to_q_2 = 'I am also an entry'
    q = NukeBoxQueue()
    q.append(to_q_1)
    q.append(to_q_2)
    if len(q) is not 0:
        print('Q Not Empty')
    result_1 = q.popleft()
    print('Result 1 is ' + result_1)
    print(str(q))
    result_2 = q.popleft()
    print('Result 2 is ' + result_2)


# # Output
# Inside Deque Module: Value: I am an entry
# Added to Queue
# deque(['I am an entry'])
# Queue Length Currently 1
# Q not empty
# Queue Now Empty
# I am an entry


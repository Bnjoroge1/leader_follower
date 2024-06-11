import unittest
import sys
sys.path.append('../protocol')
from network_classes import Node

def worker():
    pass
    # send the test child processes here

class TestNode(unittest.TestCase):

    def testConstructor(self):
        node1 = Node(1)
        self.assertEqual(node1.node_id, 1)

        hash_val = node1.__hash__() % 100000000
        self.assertEqual(node1.thisDevice.id, hash_val)

    def testProcessStartStop(self):
        pass
        # create one transceiver and test child process starts/stops, no zombies

    def testProcessSendBetweenTwoProcesses(self):
        pass
        # test comm line created between two child processes
        # test send/receive works between processes

    def testProcessSendBetweenMultipleProcesses(self):
        pass
        # test three comm lines created and can send individually
        # test can send multiple (for attendance)

if __name__ == '__main__':
    unittest.main()


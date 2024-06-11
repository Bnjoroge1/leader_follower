import unittest
from time import sleep
import multiprocessing
import sys
sys.path.append('../protocol')
from network_classes import Node

def test_worker():
    print("child process starting...")
    sleep(3)
    print("child process ending...")
    # send the test child processes here

class TestNode(unittest.TestCase):
    # Transceiver unit tests have passed
    def testConstructor(self):
        # test with nodeid of 1, no process function passed
        node1 = Node(1, test_worker)
        self.assertEqual(node1.node_id, 1)

        hash_val = node1.__hash__() % 100000000
        self.assertEqual(node1.thisDevice.id, hash_val)

        self.assertIsInstance(node1.process, multiprocessing.Process)

        node1.process.start()
        node1.process.join()

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


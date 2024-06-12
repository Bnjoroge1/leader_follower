import unittest
from time import sleep
from signal import SIGTERM
import multiprocessing as mp
import sys
sys.path.append('../protocol')
from network_classes import Node

def test_worker():
    print("child process starting...")
    sleep(1)
    print("child process ending...")
    # send the test child processes here

def test_transmission(transceiver, node_id):
    transceiver.send(node_id)


class TestNode(unittest.TestCase):
    # Transceiver unit tests have passed
    def testConstructor(self):
        # test with nodeid of 1, no process function passed
        node1 = Node(1, test_worker)
        self.assertEqual(node1.node_id, 1)

        # check hash is correct
        hash_val = node1.__hash__() % 100000000
        self.assertEqual(node1.thisDevice.id, hash_val)

        # check process created works
        self.assertIsInstance(node1.process, mp.Process)
        node1.process.start()
        self.assertTrue(node1.process.is_alive())
        node1.process.join()
        self.assertFalse(node1.process.is_alive())

    def testProcessStartStop(self):
        node = Node(1, test_worker)
        node.start()
        self.assertTrue(node.process.is_alive())
        node.stop()
        # small delay because it takes a second for terminate to execute
        sleep(0.1)
        self.assertFalse(node.process.is_alive())
        self.assertEqual(node.process.exitcode, -SIGTERM)

    def testProcessSendBetweenTwoProcesses(self):
        node1 = Node(1, test_transmission, "not none")
        node2 = Node(2, test_transmission, "not none")

        q1 = mp.Queue() # 1 to 2
        q2 = mp.Queue() # 2 to 1

        node1.set_outgoing_channel(2, q1)
        node1.set_incoming_channel(2, q2)

        node2.set_outgoing_channel(1, q2)
        node2.set_incoming_channel(1, q1)

        node1.start()
        node2.start()

        node1.join()
        node2.join()

        self.assertFalse(node1.transceiver.incoming_channels[2].empty())
        self.assertFalse(node2.transceiver.incoming_channels[1].empty())

        result1 = node1.transceiver.receive(2)
        result2 = node2.transceiver.receive(2)

        self.assertEqual(result1, 2)
        self.assertEqual(result2, 1)

    def testProcessSendBetweenMultipleProcesses(self):
        pass
        # test three comm lines created and can send individually
        # test can send multiple (for attendance)

if __name__ == '__main__':
    unittest.main()


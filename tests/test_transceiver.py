import unittest
import queue
import sys
from base_test import PROTOCOL_DIR
sys.path.append(str(PROTOCOL_DIR))
from simulation_network import SimulationTransceiver

class TestTransceiver(unittest.TestCase):

    def setUp(self):
        # nodeid=1
        self.transceiver1 = SimulationTransceiver()
        # nodeid=2
        self.transceiver2 = SimulationTransceiver()

        q1 = queue.Queue() # 1 to 2
        q2 = queue.Queue() # 2 to 1

        self.transceiver1.set_outgoing_channel(2, q1)
        self.transceiver1.set_incoming_channel(2, q2)

        self.transceiver2.set_outgoing_channel(1, q2)
        self.transceiver2.set_incoming_channel(1, q1)

    def testSetMethods(self):
        out_len = len(self.transceiver1.outgoing_channels)
        in_len = len(self.transceiver1.incoming_channels)
        self.assertEqual(out_len, 1)
        self.assertEqual(in_len, 1)

        test1 = "test outgoing 1"
        # put into q1 via transceiver 1
        self.transceiver1.outgoing_channels[2].put(test1)
        # get out via transceiver 1
        result1 = self.transceiver1.outgoing_channels[2].get()
        # make sure result is correct
        self.assertEqual(result1, test1, "Outgoing channel from 1->2 input from 1 failed")
        # make sure q1 is empty
        self.assertTrue(self.transceiver1.outgoing_channels[2].empty())

        test2 = "test incoming 1"
        # put into q1 via transceiver 1
        self.transceiver1.outgoing_channels[2].put(test2)
        # get out via transceiver 2
        result2 = self.transceiver2.incoming_channels[1].get()
        # make sure result is correct
        self.assertEqual(result2, test2, "Incoming channel from 1->2 input from 1 failed")
        # make sure empty afterwards
        self.assertTrue(self.transceiver1.outgoing_channels[2].empty())

    def testSendWithTwoDevices(self):
        # send via transceiver 1
        test1 = 1234
        self.transceiver1.send(test1)
        # check message is in appropriate incoming channel in transceiver 2
        result1 = self.transceiver2.incoming_channels[1].get()
        self.assertEqual(result1, test1)

        test2 = 4321
        self.transceiver2.send(test2)
        result2 = self.transceiver1.incoming_channels[2].get()
        self.assertEqual(result2, test2)

    def testSendWithMultipleDevices(self):
        # nodeid=3
        self.transceiver3 = SimulationTransceiver()

        q3 = queue.Queue() # 1 to 3
        q4 = queue.Queue() # 3 to 1
        q5 = queue.Queue() # 2 to 3
        q6 = queue.Queue() # 3 to 2

        self.transceiver1.set_outgoing_channel(3, q3)
        self.transceiver1.set_incoming_channel(3, q4)

        self.transceiver2.set_outgoing_channel(3, q5)
        self.transceiver2.set_incoming_channel(3, q6)

        self.transceiver3.set_outgoing_channel(1, q4)
        self.transceiver3.set_outgoing_channel(2, q6)
        self.transceiver3.set_incoming_channel(1, q3)
        self.transceiver3.set_incoming_channel(2, q5)

        test1 = 5678
        self.transceiver1.send(test1)
        result_t2 = self.transceiver2.incoming_channels[1].get()
        result_t3 = self.transceiver3.incoming_channels[1].get()
        self.assertEqual(result_t2, test1, "t2 failed")
        self.assertEqual(result_t3, test1, "t3 failed")

    def testReceive(self):
        test1 = 8765
        self.transceiver1.outgoing_channels[2].put(test1)
        result1 = self.transceiver2.receive(None)
        self.assertEqual(result1, test1)
    

if __name__ == '__main__':
    unittest.main()


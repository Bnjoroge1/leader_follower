import unittest
from time import sleep
from signal import SIGTERM
import multiprocessing as mp
import sys
from base_test import PROTOCOL_DIR
sys.path.append(str(PROTOCOL_DIR))
from simulation_network import SimulationNode

def test_worker():
    print("child process starting...")
    sleep(1)
    print("child process ending...")
    # send the test child processes here

def test_transmission(transceiver, node_id):
    print("sending")
    transceiver.send(node_id)

def test_send_and_receive(transceiver, node_id):
    print("sending")
    transceiver.send(node_id)
    sleep(1)
    result = transceiver.receive(2)
    print(result)

class TestNode(unittest.TestCase):
    # Transceiver unit tests have passed
    def testConstructor(self):
        # test with nodeid of 1, no process function passed
        node1 = SimulationNode(1, test_worker)
        self.assertEqual(node1.node_id, 1)

        # check hash is correct
       # hash_val = node1.generate_device_id(1)
        hash_cal = node1.__hash__() % 10000
        self.assertEqual(node1.thisDevice.id, hash_cal)

        # check process created works
        self.assertIsInstance(node1.process, mp.Process)
        node1.process.start()
        self.assertTrue(node1.process.is_alive())
        node1.process.join()
        self.assertFalse(node1.process.is_alive())

    def testProcessStartStop(self):
        node = SimulationNode(1, test_worker)
        node.start()
        self.assertTrue(node.process.is_alive())
        node.stop()
        # small delay because it takes a second for terminate to execute
        sleep(0.1)
        self.assertFalse(node.process.is_alive())
        self.assertEqual(node.process.exitcode, -SIGTERM)

    # def testProcessSendBetweenTwoProcesses(self):
    #     node1 = SimulationNode(1, test_transmission, "not none")
    #     node2 = SimulationNode(2, test_transmission, "not none")

    #     q1 = mp.Queue() # 1 to 2
    #     q2 = mp.Queue() # 2 to 1

    #     node1.set_outgoing_channel(2, q1)
    #     node1.set_incoming_channel(2, q2)

    #     node2.set_outgoing_channel(1, q2)
    #     node2.set_incoming_channel(1, q1)

    #     node1.start()
    #     node2.start()

    #     node1.join()
    #     node2.join()

    #     self.assertFalse(node1.transceiver.incoming_channels[2].empty())
    #     self.assertFalse(node2.transceiver.incoming_channels[1].empty())

    #     result1 = node1.transceiver.receive(2)
    #     result2 = node2.transceiver.receive(2)

    #     self.assertEqual(result1, 2)
    #     self.assertEqual(result2, 1)
    def testIdGenerationIssues(self):
        # Test inconsistency across recreations
        print("Testing inconsistency across recreations")
        node1 = SimulationNode(1, test_worker)
        id1 = node1.thisDevice.id
        
        node1_recreated = SimulationNode(1, test_worker)
        id1_recreated = node1_recreated.thisDevice.id
        
        print(f"Original node 1 ID: {id1}")
        print(f"Recreated node 1 ID: {id1_recreated}")
        
        self.assertNotEqual(id1, id1_recreated, "IDs should be different for recreated nodes")

        # Test potential for collisions
        ids = set()
        collisions = 0
        for i in range(10000):
            node = SimulationNode(i, test_worker)
            if node.thisDevice.id in ids:
                collisions += 1
            ids.add(node.thisDevice.id)
        
        collision_percentage = (collisions / 10000) * 100
        print(f"Number of ID collisions: {collisions}")
        print(f"Collision percentage: {collision_percentage:.2f}%")
        
        self.assertGreater(collisions, 0, "There should be some ID collisions")

    # Test inconsistency across different runs
        print(f"Current ID for node 1: {id1}")
        print("Run this test multiple times to see how the IDs change between runs.")
    def testIdCollisionsInSmallerRange(self):
        # Test potential for collisions in a smaller range
        print("Testing ID collisions in a smaller range")
        ids = set()
        collisions = 0
        range_size = 1000
        iterations = 10000

        for _ in range(iterations):
            node = SimulationNode(_ % range_size, test_worker)
            if node.thisDevice.id in ids:
                collisions += 1
            ids.add(node.thisDevice.id)
        
        collision_percentage = (collisions / iterations) * 100
        print(f"Number of ID collisions in range {range_size}: {collisions}")
        print(f"Collision percentage: {collision_percentage:.2f}%")
        
        self.assertGreater(collisions, 0, "There should be some ID collisions in a smaller range")
        self.assertLess(len(ids), iterations, "Not all IDs should be unique in a smaller range")

        # Test for potential bias in ID distribution
        id_counts = {i: 0 for i in range(range_size)}
        for id in ids:
            id_counts[id % range_size] += 1
        
        max_count = max(id_counts.values())
        min_count = min(id_counts.values())
        spread = max_count - min_count
        
        print(f"Max occurrences of any ID: {max_count}")
        print(f"Min occurrences of any ID: {min_count}")
        print(f"Spread of occurrences: {spread}")
    
        self.assertGreater(spread, iterations / (range_size * 10), "Distribution of IDs should show some bias")
    # def testIdGeneration2(self):
    #     # Test consistency across recreations
    #     node1 = SimulationNode(1, test_worker)
    #     id1 = node1.thisDevice.id
        
    #     node1_recreated = SimulationNode(1, test_worker)
    #     id1_recreated = node1_recreated.thisDevice.id
        
    #     print(f"Original node 1 ID: {id1}")
    #     print(f"Recreated node 1 ID: {id1_recreated}")
        
    #     self.assertEqual(id1, id1_recreated, "IDs should be the same for recreated nodes")

    #     # Test uniqueness
    #     ids = set()
    #     for i in range(10000):
    #         node = SimulationNode(i, test_worker)
    #         ids.add(node.thisDevice.id)
        
    #     print(f"Number of unique IDs: {len(ids)}")
    #     self.assertEqual(len(ids), 10000, "All 10000 IDs should be unique")

    #     # Test consistency across different runs
    #     print(f"ID for node 1: {id1}")
    #     print("This ID should be the same across different runs.")
    def testProcessReceiveBetweenTwoProcesses(self):
        pass

    def testProcessSendBetweenMultipleProcesses(self):
        pass
        # test three comm lines created and can send individually
        # test can send multiple (for attendance)

if __name__ == '__main__':
    unittest.main()


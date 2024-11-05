import unittest
import time
from simulation_network import SimulationNode, Network
from message_classes import Action
import csv

class test_tiebreak_protocol(unittest.TestCase):
    
    def setUp(self):
        self.leader = SimulationNode(1)
        self.conflict = SimulationNode(2)
        self.extra = SimulationNode(3)

        self.network = Network()
        self.network.add_node(1, self.leader)
        self.network.add_node(2, self.conflict)
        self.network.add_node(3, self.extra)

        self.network.create_channel(1, 2)
        self.network.create_channel(1, 3)
        self.network.create_channel(2, 3)

        self.leader_file_name = f'output/device_log_{self.leader.thisDevice.id}.csv'
        self.conflict_file_name = f'output/device_log_{self.conflict.thisDevice.id}.csv'
        self.extra_file_name = f'output/device_log_{self.extra.thisDevice.id}.csv'
    
    def correct_leader_chosen_from_attendance(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.conflict.set_process(self.conflict.thisDevice.test_tiebreak_conflicting_leader_sends_after_attendance)
        self.extra.set_process(self.extra.thisDevice.device_main)
        
        self.leader.start()
        time.sleep(3)
        self.extra.start()
        self.sleep(3)
        self.conflict.start()
        
        time.sleep(10)
        
        self.leader.stop()
        self.conflict.stop()
        self.extra.stop()
        
        if self.leader.thisDevice.id > self.conflict.thisDevice.id and self.leader.thisDevice.id > self.extra.thisDevice.id:
            self.assertTrue(self.leader.thisDevice.leader)
            self.assertEqual(self.conflict.thisDevice.leader_id, self.leader.thisDevice.id)
            self.assertEqual(self.extra.thisDevice.leader_id, self.leader.thisDevice.id)
        elif self.conflict.thisDevice.id > self.leader.thisDevice.id and self.conflict.thisDevice.id > self.extra.thisDevice.id:
            self.assertTrue(self.conflict.thisDevice.leader)
            self.assertEqual(self.leader.thisDevice.leader_id, self.conflict.thisDevice.id)
            self.assertEqual(self.extra.thisDevice.leader_id, self.conflict.thisDevice.id)
        else:
            self.assertTrue(self.extra.thisDevice.leader)
            self.assertEqual(self.leader.thisDevice.leader_id, self.extra.thisDevice.id)
            self.assertEqual(self.conflict.thisDevice.leader_id, self.extra.thisDevice.id)
            
    
    def correct_leader_chosen_from_check_in(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.conflict.set_process(self.conflict.thisDevice.test_tiebreak_conflicting_leader_sends_after_check_in)
        self.extra.set_process(self.extra.thisDevice.device_main)
        
        self.leader.start()
        time.sleep(3)
        self.extra.start()
        self.sleep(3)
        self.conflict.start()
        
        time.sleep(10)
        
        self.leader.stop()
        self.conflict.stop()
        self.extra.stop()
        
        if self.leader.thisDevice.id > self.conflict.thisDevice.id and self.leader.thisDevice.id > self.extra.thisDevice.id:
            self.assertTrue(self.leader.thisDevice.leader)
            self.assertEqual(self.conflict.thisDevice.leader_id, self.leader.thisDevice.id)
            self.assertEqual(self.extra.thisDevice.leader_id, self.leader.thisDevice.id)
        elif self.conflict.thisDevice.id > self.leader.thisDevice.id and self.conflict.thisDevice.id > self.extra.thisDevice.id:
            self.assertTrue(self.conflict.thisDevice.leader)
            self.assertEqual(self.leader.thisDevice.leader_id, self.conflict.thisDevice.id)
            self.assertEqual(self.extra.thisDevice.leader_id, self.conflict.thisDevice.id)
        else:
            self.assertTrue(self.extra.thisDevice.leader)
            self.assertEqual(self.leader.thisDevice.leader_id, self.extra.thisDevice.id)
            self.assertEqual(self.conflict.thisDevice.leader_id, self.extra.thisDevice.id)
        
    
    def correct_leader_chosen_out_of_three_conflicting(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.conflict.set_process(self.conflict.thisDevice.test_tiebreak_conflicting_leader_sends_after_attendance)
        self.extra.set_process(self.extra.thisDevice.test_tiebreak_conflicting_leader_sends_after_attendance)
        
        self.leader.start()
        time.sleep(3)
        self.extra.start()
        self.conflict.start()
        
        time.sleep(10)
        
        self.leader.stop()
        self.conflict.stop()
        self.extra.stop()
        
        if self.leader.thisDevice.id > self.conflict.thisDevice.id and self.leader.thisDevice.id > self.extra.thisDevice.id:
            self.assertTrue(self.leader.thisDevice.leader)
            self.assertEqual(self.conflict.thisDevice.leader_id, self.leader.thisDevice.id)
            self.assertEqual(self.extra.thisDevice.leader_id, self.leader.thisDevice.id)
        elif self.conflict.thisDevice.id > self.leader.thisDevice.id and self.conflict.thisDevice.id > self.extra.thisDevice.id:
            self.assertTrue(self.conflict.thisDevice.leader)
            self.assertEqual(self.leader.thisDevice.leader_id, self.conflict.thisDevice.id)
            self.assertEqual(self.extra.thisDevice.leader_id, self.conflict.thisDevice.id)
        else:
            self.assertTrue(self.extra.thisDevice.leader)
            self.assertEqual(self.leader.thisDevice.leader_id, self.extra.thisDevice.id)
            self.assertEqual(self.conflict.thisDevice.leader_id, self.extra.thisDevice.id)
        
    
    def correct_leader_chosen_out_of_five_conflicting(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.conflict.set_process(self.conflict.thisDevice.test_tiebreak_conflicting_leader_sends_after_attendance)
        self.extra.set_process(self.extra.thisDevice.test_tiebreak_conflicting_leader_sends_after_attendance)
        extra2 = SimulationNode(4)
        extra3 = SimulationNode(5)
        self.network.add_node(4, extra2)
        self.network.add_node(5, extra3)
        self.network.create_channel(1,4)
        self.network.create_channel(2,4)
        self.network.create_channel(3,4)
        self.network.create_channel(1,5)
        self.network.create_channel(2,5)
        self.network.create_channel(3,5)
        self.network.create_channel(4,5)
        extra2.set_process(extra2.thisDevice.test_tiebreak_conflicting_leader_sends_after_attendance)
        extra3.set_process(extra3.thisDevice.test_tiebreak_conflicting_leader_sends_after_attendance)
        
        self.leader.start()
        time.sleep(3)
        self.extra.start()
        self.conflict.start()
        extra2.start()
        extra3.start()
        
        time.sleep(10)
        
        self.leader.stop()
        self.conflict.stop()
        self.extra.stop()
        extra2.stop()
        extra3.stop()
        
        nodes = [self.leader, self.conflict, self.extra, extra2, extra3]
        highest_node = None
        highest = 0
        for node in nodes:
            if node.thisDevice.id > highest:
                highest = node.thisDevice.id
                highest_node = node
        
        for node in nodes:
            if node == highest_node:
                self.assertTrue(node.thisDevice.leader)
            else:
                self.assertEqual(node.thisDevice.leader_id, highest_node.thisDevice.id)
                
if __name__ == '__main__':
    unittest.main()
            
            
            
            
            
            
            
            
            
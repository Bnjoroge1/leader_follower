import unittest
import time
from simulation_network import SimulationNode, Network
from message_classes import Action
import csv

class test_takeover_protocol(unittest.TestCase):
    
    def setUp(self):
        self.leader = SimulationNode(1)
        self.follower = SimulationNode(2)
        self.extra = SimulationNode(3)

        self.network = Network()
        self.network.add_node(1, self.leader)
        self.network.add_node(2, self.follower)
        self.network.add_node(3, self.extra)

        self.network.create_channel(1, 2)
        self.network.create_channel(1, 3)
        self.network.create_channel(2, 3)

        self.leader_file_name = f'output/device_log_{self.leader.thisDevice.id}.csv'
        self.follower_file_name = f'output/device_log_{self.follower.thisDevice.id}.csv'
        self.extra_file_name = f'output/device_log_{self.extra.thisDevice.id}.csv'

    def follower_in_setup_takes_over_when_leader_drops_and_no_other_devices_present(self):
        # send leader process to setup trap - will send d_list then drop
        self.leader.set_process(self.leader.thisDevice.test_takeover_leader_sends_one_message)
        # send follower to main
        self.follower.set_process(self.follower.thisDevice.device_main)

        self.leader.start()
        self.follower.start()

        # takes 15 seconds to become leader + 4 for attendance
        time.sleep(20)

        self.leader.stop()
        self.follower.stop()

        with open(self.follower_file_name) as follower_logs:
            follower_reader = csv.reader(follower_logs)

            # conditions to see in logs
            received_d_list = False
            correct_takeover = False

            for line in follower_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_action = msg // int(1e10)
                    if msg_action == Action.D_LIST.value:
                        received_d_list = True
                if line[1] == "STATUS":
                    if line[2] == "BECAME LEADER":
                        correct_takeover = True

            # check all conditions met
            self.assertTrue(received_d_list, "Never heard d_list")
            self.assertFalse(correct_takeover, "Heard some attendance")
    
    def follower_in_setup_follows_new_leader_if_other_devices_present(self):
        # send leader process to setup trap - will send d_list then drop
        self.leader.set_process(self.leader.thisDevice.test_takeover_leader_sends_one_message)
        self.extra.set_process(self.extra.thisDevice.device_main)
        # send follower to main
        self.follower.set_process(self.follower.thisDevice.device_main)

        self.leader.start()
        self.extra.start()
        time.sleep(5)
        self.follower.start()

        # takes 15 seconds to become leader + 4 for attendance
        time.sleep(20)

        self.leader.stop()
        self.follower.stop()

        with open(self.follower_file_name) as follower_logs:
            follower_reader = csv.reader(follower_logs)

            # conditions to see in logs
            received_att = False
            became_follower = False

            for line in follower_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_action = msg // int(1e10)
                    if msg_action == Action.ATTENDANCE.value:
                        received_att = True
                if line[1] == "STATUS":
                    if line[2] == "BECAME FOLLOWER":
                        became_follower = True

            # check all conditions met
            self.assertTrue(received_att, "Never heard d_list")
            self.assertFalse(became_follower, "Heard some attendance")
    
    def follower_in_main_takes_over_when_leader_drops(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.extra.set_process(self.extra.thisDevice.device_main)
        # send follower to main
        self.follower.set_process(self.follower.thisDevice.device_main)
        
        self.leader.start()
        time.sleep(3)
        self.follower.start()
        self.extra.start()
        
        self.leader.stop()
        time.sleep(20)
        self.follower.stop()
        self.extra.stop()
        
        if self.follower.thisDevice.id > self.extra.thisDevice.id:
            with open(self.follower_file_name) as follower_logs:
                follower_reader = csv.reader(follower_logs)
    
                # conditions to see in logs
                became_leader = False
    
                for line in follower_reader:
                    if line[1] == "STATUS":
                        if line[2] == "BECAME LEADER":
                            became_leader = True
    
                # check all conditions met
                self.assertTrue(became_leader, "Never heard d_list")
            with open(self.extra_file_name) as extra_logs:
                extra_reader = csv.reader(extra_logs)
    
                # conditions to see in logs
                became_follower = False
    
                for line in extra_reader:
                    if line[1] == "STATUS":
                        if line[2] == "BECAME FOLLOWER":
                            became_follower = True
    
                # check all conditions met
                self.assertTrue(became_follower, "Never heard d_list")
        else:
            with open(self.extra_file_name) as extra_logs:
                extra_reader = csv.reader(extra_logs)
    
                # conditions to see in logs
                became_leader = False
    
                for line in extra_reader:
                    if line[1] == "STATUS":
                        if line[2] == "BECAME LEADER":
                            became_leader = True
    
                # check all conditions met
                self.assertTrue(became_leader, "Never heard d_list")
            with open(self.follower_file_name) as follower_logs:
                follower_reader = csv.reader(follower_logs)
    
                # conditions to see in logs
                became_follower = False
    
                for line in follower_reader:
                    if line[1] == "STATUS":
                        if line[2] == "BECAME FOLLOWER":
                            became_follower = True
    
                # check all conditions met
                self.assertTrue(became_follower, "Never heard d_list")
    
    def new_leader_assigns_correct_task_after_leader_drops_no_reserves(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.extra.set_process(self.extra.thisDevice.device_main)
        # send follower to main
        self.follower.set_process(self.follower.thisDevice.device_main)
        new = SimulationNode(4)
        # extra node to join after leader drops and take its task
        new_node = SimulationNode(4)
        self.network.add_node(4, new_node)
        self.network.create_channel(4, 2)
        self.network.create_channel(4, 3)
        new_node.set_process(new_node.thisDevice.device_main)
        
        self.leader.start()
        time.sleep(3)
        self.follower.start()
        self.extra.start()
        self.leader.stop()
        time.sleep(20)
        
        new_node.start()
        time.sleep(5)
        self.follower.stop()
        self.extra.stop()
        new_node.stop()
        new_file_name = f'output/device_log_{new_node.thisDevice.id}.csv'
        
        with open(new_file_name) as new_logs:
            new_reader = csv.reader(new_logs)

            # conditions to see in logs
            received_leaders_task = False

            for line in new_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_action = msg // int(1e10)
                    msg_follower = msg % int(1e4)
                    msg_task = msg % int(1e10) // int(1e8)
                    
                    if msg_action == Action.D_LIST.value and msg_follower == new_node.thisDevice.id and msg_task == 1:
                        received_leaders_task = True

            # check all conditions met
            self.assertTrue(received_leaders_task, "Never heard d_list")
        
    
    def new_leader_assigns_correct_task_after_leader_drops_with_reserves(self):
        # initialize all nodes
        nodes = []
        for i in range(9):
            nodes[i] = SimulationNode(i+4)
        # add all nodes to network
        for j in range(9):
            self.network.add_node(j+4, nodes[j])
        # create a channel for all nodes to leader (interconnections between nodes not necessary here)
        for k in range(9):
            self.network.create_channel(1, k+4)
        
        # send all processes to main protocol
        self.leader.set_process(self.leader.thisDevice.device_main)
        for l in range(9):
            nodes[l].set_process(nodes[l].thisDevice.device_main)
        
        # start all devices - reserve should be device at index 8
        self.leader.start()
        time.sleep(5)
        for m in range(9):
            nodes[m].start()
            time.sleep(3)
            
        # stop leader
        self.leader.stop()
        # wait for takeover + new task assignment
        time.sleep(20)
        
        # stop all device
        for n in range(9):
            nodes[n].stop()
            
        reserve_file_name = f'output/device_log_{nodes[8].thisDevice.id}.csv'
        
        with open(reserve_file_name) as reserve_logs:
            reserve_reader = csv.reader(reserve_logs)

            # conditions to see in logs
            received_leaders_task = False

            for line in reserve_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_action = msg // int(1e10)
                    msg_follower = msg % int(1e4)
                    msg_task = msg % int(1e10) // int(1e8)
                    
                    if msg_action == Action.TASK_START.value and msg_follower == nodes[8].thisDevice.id and msg_task == 1:
                        received_leaders_task = True

            # check all conditions met
            self.assertTrue(received_leaders_task, "Never heard d_list")
    
if __name__ == '__main__':
    unittest.main()    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
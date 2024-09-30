import unittest
import time
from simulation_network import SimulationNode, Network
from message_classes import Action
import csv

# TODO: clean up
class test_attendance_protocol(unittest.TestCase):
    
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

    def test_leader_adds_device_and_sends_d_list(self):
        """
        Establish that a leader device following the main protocol will send d_list
        after a follower has responded.

        Returns
        -------
        None.

        """
        # send leader process to main 
        self.leader.set_process(self.leader.thisDevice.device_main)
        # start leader
        self.leader.start()
        # start follower - send to specialized follower
        self.follower.set_process(self.follower.thisDevice.add_device_follower)
        self.follower.start()
        time.sleep(8)
        # stop both devices
        self.leader.stop()
        self.follower.stop()

        # check logs to confirm follower had correct behavior
        # should be receive attendance message -> become follower
        with open(self.follower_file_name) as follower_logs:
            follower_reader = csv.reader(follower_logs)

            # conditions to see in logs
            corr_leader_rcvd = False
            received_att = False
            d_list_leader_received = False
            d_list_follow_received = False

            for line in follower_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_leader = msg % int(1e8) // int(1e4)
                    msg_action = msg // int(1e10)
                    msg_follower = msg % int(1e4)
                    if msg_leader == self.leader.thisDevice.id:
                        corr_leader_rcvd = True
                    if msg_action == 1:
                        received_att = True
                    if msg_action == 3:
                        if msg_follower == self.leader.thisDevice.id:
                            d_list_leader_received = True
                        elif msg_follower == self.follower.thisDevice.id:
                            d_list_follow_received = True

            # check all conditions met
            self.assertTrue(corr_leader_rcvd, "Correct leader never heard")
            self.assertTrue(received_att, "Never heard attendance")
            self.assertTrue(d_list_leader_received, "Leader did not send d_list for itself")
            self.assertTrue(d_list_follow_received, "Leader did not send d_list for follower") 
    
    def test_follower_added_from_attendance(self):
        """
        Establish that a leader device will recognize a follower response to attendance
        and add it to its d_list and assign it a task.

        Returns
        -------
        None.

        """
        # send leader process to attendance only 
        self.leader.set_process(self.leader.thisDevice.device_main)
        # start leader
        self.leader.start()
        # wait to for leader to be solidified
        time.sleep(10)
        # start follower - send to device main
        self.follower.set_process(self.follower.thisDevice.device_main)
        self.follower.start()
        # wait 5s
        time.sleep(10)
        # stop both devices
        self.leader.stop()
        self.follower.stop()

        # check logs to confirm follower had correct behavior
        # should be receive attendance message -> become follower
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)

            # conditions to see in logs
            corr_response_rcvd = False
            corr_follower_rcvd = False
            corr_leader_addr = False
            sent_d_list_follower = False
            sent_d_list_leader = False

            for line in leader_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_leader = msg % int(1e8) // int(1e4)
                    msg_action = msg // int(1e10)
                    msg_follower = msg % int(1e4)
                    
                    if msg_action == 2:
                        corr_response_rcvd = True
                        if msg_leader == self.leader.thisDevice.id:
                            corr_leader_addr = True
                        if msg_follower == self.follower.thisDevice.id:
                            corr_follower_rcvd = True
                if line[1] == "MSG SEND":
                    msg = int(line[2])
                    msg_leader = msg % int(1e8) // int(1e4)
                    msg_action = msg // int(1e10)
                    msg_follower = msg % int(1e4)

                    if msg_action == 3:
                        if msg_follower == self.leader.thisDevice.id:
                            sent_d_list_leader = True
                        if msg_follower == self.follower.thisDevice.id:
                            sent_d_list_follower = True


            # check all conditions met
            self.assertTrue(corr_response_rcvd, "Correct leader never heard")
            self.assertTrue(corr_leader_addr, "Never heard attendance")
            self.assertTrue(corr_follower_rcvd, "Leader did not send d_list for itself")
            self.assertTrue(sent_d_list_follower, "Leader did not send d_list for follower") 
            self.assertTrue(sent_d_list_leader, "Leader did not send d_list for follower")

    def test_leader_ignores_att_msg_leader_addr_correct(self):
        """
        Establish that a leader device will ignore an attendance message, given that
        the leader address is correct.

        Returns
        -------
        None.

        """
        # send leader process to attendance only 
        self.leader.set_process(self.leader.thisDevice.device_main)
        # start leader
        self.leader.start()
        # wait to for leader to be in attendance
        time.sleep(4)
        # start follower - send to device main
        self.follower.set_process(self.follower.thisDevice.att_test_invalid_msg_att)
        self.follower.start()
        # wait 5s
        time.sleep(10)
        # stop both devices
        self.leader.stop()
        self.follower.stop()

        # check logs to confirm follower had correct behavior
        # should be receive attendance message -> become follower
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)

            # conditions to see in logs
            corr_response_rcvd = False
            corr_leader_addr = False

            for line in leader_reader:
                if line[1] == "MSG IGNORED":
                    msg = int(line[2])
                    msg_leader = msg % int(1e8) // int(1e4)
                    msg_action = msg // int(1e10)
                    
                    if msg_action == 1:
                        corr_response_rcvd = True
                        if msg_leader == self.leader.thisDevice.id:
                            corr_leader_addr = True


            # check all conditions met
            self.assertTrue(corr_response_rcvd, "Correct leader never heard")
            self.assertTrue(corr_leader_addr, "Never heard attendance")

    def test_leader_ignores_d_list_msg_leader_addr_correct(self):
        """
        Establish that a leader device will ignore a d_list message, given that
        the leader address is correct.

        Returns
        -------
        None.

        """
        # send leader process to attendance only 
        self.leader.set_process(self.leader.thisDevice.device_main)
        # start leader
        self.leader.start()
        # wait to for leader to be in attendance
        time.sleep(4)
        # start follower - send to device main
        self.follower.set_process(self.follower.thisDevice.att_test_invalid_msg_d_list)
        self.follower.start()
        # wait 5s
        time.sleep(10)
        # stop both devices
        self.leader.stop()
        self.follower.stop()

        # check logs to confirm follower had correct behavior
        # should be receive attendance message -> become follower
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)

            # conditions to see in logs
            corr_response_rcvd = False
            corr_leader_addr = False

            for line in leader_reader:
                if line[1] == "MSG IGNORED":
                    msg = int(line[2])
                    msg_leader = msg % int(1e8) // int(1e4)
                    msg_action = msg // int(1e10)
                    
                    if msg_action == 3:
                        corr_response_rcvd = True
                        if msg_leader == self.leader.thisDevice.id:
                            corr_leader_addr = True


            # check all conditions met
            self.assertTrue(corr_response_rcvd, "Correct leader never heard")
            self.assertTrue(corr_leader_addr, "Never heard attendance")
    
    def test_leader_ignores_check_in_msg_leader_addr_correct(self):
        """
        Establish that a leader device will ignore a check in message, given that
        the leader address is correct.

        Returns
        -------
        None.

        """
        # send leader process to attendance only 
        self.leader.set_process(self.leader.thisDevice.device_main)
        # start leader
        self.leader.start()
        # wait to for leader to be in attendance
        time.sleep(4)
        # start follower - send to device main
        self.follower.set_process(self.follower.thisDevice.att_test_invalid_msg_check_in)
        self.follower.start()
        # wait 5s
        time.sleep(10)
        # stop both devices
        self.leader.stop()
        self.follower.stop()

        # check logs to confirm follower had correct behavior
        # should be receive attendance message -> become follower
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)

            # conditions to see in logs
            corr_response_rcvd = False
            corr_leader_addr = False

            for line in leader_reader:
                if line[1] == "MSG IGNORED":
                    msg = int(line[2])
                    msg_leader = msg % int(1e8) // int(1e4)
                    msg_action = msg // int(1e10)
                    
                    if msg_action == 4:
                        corr_response_rcvd = True
                        if msg_leader == self.leader.thisDevice.id:
                            corr_leader_addr = True


            # check all conditions met
            self.assertTrue(corr_response_rcvd, "Correct leader never heard")
            self.assertTrue(corr_leader_addr, "Never heard attendance")

    def test_leader_ignores_delete_msg_leader_addr_correct(self):
        """
        Establish that a leader device will ignore a delete message, given that
        the leader address is correct.

        Returns
        -------
        None.

        """
        # send leader process to attendance only 
        self.leader.set_process(self.leader.thisDevice.device_main)
        # start leader
        self.leader.start()
        # wait to for leader to be in attendance
        time.sleep(4)
        # start follower - send to device main
        self.follower.set_process(self.follower.thisDevice.att_test_invalid_msg_delete)
        self.follower.start()
        # wait 5s
        time.sleep(10)
        # stop both devices
        self.leader.stop()
        self.follower.stop()

        # check logs to confirm follower had correct behavior
        # should be receive attendance message -> become follower
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)

            # conditions to see in logs
            corr_response_rcvd = False
            corr_leader_addr = False

            for line in leader_reader:
                if line[1] == "MSG IGNORED":
                    msg = int(line[2])
                    msg_leader = msg % int(1e8) // int(1e4)
                    msg_action = msg // int(1e10)
                    
                    if msg_action == 5:
                        corr_response_rcvd = True
                        if msg_leader == self.leader.thisDevice.id:
                            corr_leader_addr = True


            # check all conditions met
            self.assertTrue(corr_response_rcvd, "Correct leader never heard")
            self.assertTrue(corr_leader_addr, "Never heard attendance")
            
    def test_leader_assigns_all_tasks_in_numerical_order_then_reserves(self):
        """
        Establish that a leader device will send each device that joins a task in 
        sequential order, and once no more tasks remain, assign new devices as reserves.

        Returns
        -------
        None.

        """
        
        
        # initialize all nodes
        nodes = []
        for i in range(10):
            nodes[i] = SimulationNode(i+4)
        # add all nodes to network
        for j in range(10):
            self.network.add_node(j+4, nodes[j])
        # create a channel for all nodes to leader (interconnections between nodes not necessary here)
        for k in range(10):
            self.network.create_channel(1, k+4)
        
        # send all processes to main protocol
        self.leader.set_process(self.leader.thisDevice.device_main)
        for l in range(10):
            nodes[l].set_process(nodes[l].thisDevice.device_main)
        
        # start all devices
        self.leader.start()
        time.sleep(5)
        for m in range(10):
            nodes[m].start()
            time.sleep(3)
            
        # stop all devices
        self.leader.stop()
        for n in range(10):
            nodes[n].stop()
            
            
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)

            # conditions to see in logs
            correct_task = 2
            end_task = 8
            tasks_assigned_sequentially = True
            reserves_assigned_correctly = True

            for line in leader_reader:
                if line[1] == "MSG SEND":
                    msg = int(line[2])
                    msg_action = msg // int(1e10)
                    msg_task = msg % int(1e10) // int(1e8)
                    
                    if msg_action == Action.D_LIST.value:
                        if msg_task == correct_task and msg_task <= end_task:
                            correct_task += 1
                        elif msg_task > end_task:
                            if msg_task != 0:
                                reserves_assigned_correctly = False
                        else:
                            tasks_assigned_sequentially = False
                            
            # check all conditions met
            self.assertTrue(tasks_assigned_sequentially, "Tasks not assigned in sequential order")
            self.assertTrue(reserves_assigned_correctly, "Reserves not assigned task")
            
        
        

if __name__ == '__main__':
    unittest.main()

    
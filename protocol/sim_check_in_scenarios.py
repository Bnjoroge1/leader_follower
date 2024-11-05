import unittest
import time
from simulation_network import SimulationNode, Network
from message_classes import Action
import csv

# TODO: clean up 
class test_check_in_protocol(unittest.TestCase):
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

    @unittest.skip("reduce time")
    def test_leader_checks_in_with_two_devices(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.leader.start()
        time.sleep(3)
        self.follower.set_process(self.follower.thisDevice.device_main)
        self.follower.start()
        self.extra.set_process(self.extra.thisDevice.device_main)
        self.extra.start()
        time.sleep(15)

        self.leader.stop()
        self.follower.stop()
        self.extra.stop()

        
        with open(self.follower_file_name) as follower_logs:
            follower_reader = csv.reader(follower_logs)

            # conditions to see in logs
            received_check_in_1 = False
            corr_addr_1 = False

            for line in follower_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_follower = msg % int(1e4)
                    msg_action = msg // int(1e10)
                    
                    if msg_action == 4:
                        received_check_in_1 = True
                        if msg_follower == self.follower.thisDevice.id:
                            corr_addr_1 = True


            # check all conditions met
            self.assertTrue(received_check_in_1, "Correct leader never heard")
            self.assertTrue(corr_addr_1, "Never heard attendance")

        with open(self.extra_file_name) as extra_logs:
            extra_reader = csv.reader(extra_logs)

            # conditions to see in logs
            received_check_in_2 = False
            corr_addr_2 = False

            for line in extra_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_follower = msg % int(1e4)
                    msg_action = msg // int(1e10)
                    
                    if msg_action == 4:
                        received_check_in_2 = True
                        if msg_follower == self.extra.thisDevice.id:
                            corr_addr_2 = True


            # check all conditions met
            self.assertTrue(received_check_in_2, "Correct leader never heard")
            self.assertTrue(corr_addr_2, "Never heard attendance")
    @unittest.skip("reduce time")
    def test_both_followers_answer_check_in(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.leader.start()
        time.sleep(3)
        self.follower.set_process(self.follower.thisDevice.device_main)
        self.follower.start()
        self.extra.set_process(self.extra.thisDevice.device_main)
        self.extra.start()
        time.sleep(15)

        self.leader.stop()
        self.follower.stop()
        self.extra.stop()

        
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)

            # conditions to see in logs
            received_response_1 = False
            received_response_2 = False

            for line in leader_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_follower = msg % int(1e4)
                    msg_action = msg // int(1e10)
                    
                    if (msg_action == 4) and (msg_follower == self.follower.thisDevice.id):
                        received_response_1 = True
                    elif (msg_action == 4) and (msg_follower == self.extra.thisDevice.id):
                        received_response_2 = True


            # check all conditions met
            self.assertTrue(received_response_1, "Correct leader never heard")
            self.assertTrue(received_response_2, "Never heard attendance")
    @unittest.skip("reduce time")
    def test_followers_ignore_other_check_in(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.leader.start()
        time.sleep(3)
        self.follower.set_process(self.follower.thisDevice.device_main)
        self.follower.start()
        self.extra.set_process(self.extra.thisDevice.device_main)
        self.extra.start()
        time.sleep(15)

        self.leader.stop()
        self.follower.stop()
        self.extra.stop()

        
        with open(self.follower_file_name) as follower_logs:
            follower_reader = csv.reader(follower_logs)

            # conditions to see in logs
            ignored_1 = False

            for line in follower_reader:
                if line[1] == "STATUS" and line[2] == f"IGNORED: {self.extra.thisDevice.id}":
                    ignored_1 = True
                    
            # check all conditions met
            self.assertTrue(ignored_1, "Correct leader never heard")

        with open(self.extra_file_name) as extra_logs:
            extra_reader = csv.reader(extra_logs)

            # conditions to see in logs
            ignored_2 = False

            for line in extra_reader:
                if line[1] == "STATUS" and line[2] == f"IGNORED: {self.follower.thisDevice.id}":
                    ignored_2 = True


            # check all conditions met
            self.assertTrue(ignored_2, "Correct leader never heard")
        
    def test_leader_increments_missed(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.leader.start()
        time.sleep(3)
        self.follower.set_process(self.follower.thisDevice.device_main)
        self.follower.start()
        self.extra.set_process(self.extra.thisDevice.device_main)
        self.extra.start()
        time.sleep(5)
        self.follower.stop()
        time.sleep(30)
        self.leader.stop()
        self.extra.stop()

        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)

            # conditions to see in logs
            missed_1 = False
            missed_2 = False

            for line in leader_reader:
                if line[1] == "STATUS" and line[2] == "MISSED +1 = 1":
                    missed_1 = True
                
                elif missed_1 == True and line[1] == "STATUS" and line[2] == "MISSED +1 = 2":
                    missed_2 = True

            self.assertTrue(missed_1, "Correct leader never heard")
            self.assertTrue(missed_2, "Correct leader never heard")

    def test_leader_sends_delete_disconnected_device(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.leader.start()
        time.sleep(3)
        self.follower.set_process(self.follower.thisDevice.device_main)
        self.follower.start()
        self.extra.set_process(self.extra.thisDevice.device_main)
        self.extra.start()
        time.sleep(5)
        self.follower.stop()
        time.sleep(30)
        self.leader.stop()
        self.extra.stop()
        
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)

            # conditions to see in logs
            missed_1 = False
            missed_2 = False
            missed_3 = False
            
            for line in leader_reader:
                if line[1] == "STATUS" and line[2] == "MISSED +1 = 1":
                    missed_1 = True
                
                elif missed_1 and line[1] == "STATUS" and line[2] == "MISSED +1 = 2":
                    missed_2 = True
                elif missed_1 and missed_2 and line[2] == "MISSED +1 = 3": 
                    missed_3 = True

            self.assertTrue(missed_1, "Leader did not register device missing 1st check in")
            self.assertTrue(missed_2, "Leader did not register device missing 2nd check in")
            self.assertTrue(missed_3, "Leader did not register device missing 3rd check in")
            
        with open(self.extra_file_name) as extra_logs:
            extra_reader = csv.reader(extra_logs)

            # conditions to see in logs
            delete_rcvd = False
            correct_device = False
            
            for line in extra_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_follower = msg % int(1e4)
                    msg_action = msg // int(1e10)
                    
                    if msg_action == 5:
                        delete_rcvd = True
                        if msg_follower == self.follower.thisDevice.id:
                            correct_device = True

            self.assertTrue(delete_rcvd, "Listener did not receive delete from leader")
            self.assertTrue(correct_device, "Correct device was not deleted - incorrect address")

    # test where it should incr missed and where it shouldnt   
    def test_leader_only_accepts_correct_follower(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.leader.start()
        time.sleep(3)
        self.follower.set_process(self.follower.thisDevice.check_in_test_delayed_correct_follower)
        self.follower.start()
        self.extra.set_process(self.extra.thisDevice.check_in_test_rogue_device)
        self.extra.start()
        time.sleep(20)
        self.follower.stop()
        self.leader.stop()
        self.extra.stop()
        
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)
            
            received_incorrect_response = False
            ignored_incorrect_response = False
            
            for line in leader_reader:
                if line[1] == "STATUS" and line[2] == "IGNORING INCORRECT RESPONSE":
                    ignored_incorrect_response = True 
                elif line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_follower = msg % int(1e4)
                    msg_action = msg // int(1e10)
                    
                    if msg_action == 4 and msg_follower == self.extra.thisDevice.id:
                        received_incorrect_response = True

            self.assertTrue(received_incorrect_response, "Leader did not receive the incorrect follower response")
            self.assertTrue(ignored_incorrect_response, "Leader did not ignore the incorrect follower response")

    def test_leader_ignores_att_wrong_follower_addr(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.leader.start()
        time.sleep(3)
        self.follower.set_process(self.follower.thisDevice.check_in_test_delayed_correct_follower)
        self.follower.start()
        self.extra.set_process(self.extra.thisDevice.check_in_test_att_from_wrong_follower)
        self.extra.start()
        time.sleep(20)
        self.follower.stop()
        self.leader.stop()
        self.extra.stop()
        
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)
            
            received_incorrect_response = False
            ignored_incorrect_response = False
            
            for line in leader_reader:
                if line[1] == "MSG IGNORED":
                    ignored_incorrect_response = True 
                    
                    msg = int(line[2])
                    msg_follower = msg % int(1e4)
                    msg_action = msg // int(1e10)
                    
                    if msg_action == 1 and msg_follower == self.extra.thisDevice.id:
                        received_incorrect_response = True
                        
            self.assertTrue(received_incorrect_response, "Leader did not receive the incorrect follower response")
            self.assertTrue(ignored_incorrect_response, "Leader did not ignore the incorrect follower response")


    def test_leader_ignores_att_response_wrong_follower_addr(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.leader.start()
        time.sleep(3)
        self.follower.set_process(self.follower.thisDevice.check_in_test_delayed_correct_follower)
        self.follower.start()
        self.extra.set_process(self.extra.thisDevice.check_in_test_att_response_from_wrong_follower())
        self.extra.start()
        time.sleep(20)
        self.follower.stop()
        self.leader.stop()
        self.extra.stop()
        
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)
            
            received_incorrect_response = False
            ignored_incorrect_response = False
            
            for line in leader_reader:
                if line[1] == "MSG IGNORED":
                    ignored_incorrect_response = True 
                    
                    msg = int(line[2])
                    msg_follower = msg % int(1e4)
                    msg_action = msg // int(1e10)
                    
                    if msg_action == 2 and msg_follower == self.extra.thisDevice.id:
                        received_incorrect_response = True
                        
            self.assertTrue(received_incorrect_response, "Leader did not receive the incorrect follower response")
            self.assertTrue(ignored_incorrect_response, "Leader did not ignore the incorrect follower response")


    def test_leader_ignores_delete_wrong_follower_addr(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.leader.start()
        time.sleep(3)
        self.follower.set_process(self.follower.thisDevice.check_in_test_delayed_correct_follower)
        self.follower.start()
        self.extra.set_process(self.extra.thisDevice.check_in_test_d_list_from_wrong_follower)
        self.extra.start()
        time.sleep(20)
        self.follower.stop()
        self.leader.stop()
        self.extra.stop()
        
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)
            
            received_incorrect_response = False
            ignored_incorrect_response = False
            
            for line in leader_reader:
                if line[1] == "MSG IGNORED":
                    ignored_incorrect_response = True 
                    
                    msg = int(line[2])
                    msg_follower = msg % int(1e4)
                    msg_action = msg // int(1e10)
                    
                    if msg_action == 3 and msg_follower == self.extra.thisDevice.id:
                        received_incorrect_response = True
                        
            self.assertTrue(received_incorrect_response, "Leader did not receive the incorrect follower response")
            self.assertTrue(ignored_incorrect_response, "Leader did not ignore the incorrect follower response")


    def test_leader_ignores_d_list_wrong_follower_addr(self):
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.leader.start()
        time.sleep(3)
        self.follower.set_process(self.follower.thisDevice.check_in_test_delayed_correct_follower)
        self.follower.start()
        self.extra.set_process(self.extra.thisDevice.check_in_test_delete_from_wrong_follower)
        self.extra.start()
        time.sleep(20)
        self.follower.stop()
        self.leader.stop()
        self.extra.stop()
        
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)
            
            received_incorrect_response = False
            ignored_incorrect_response = False
            
            for line in leader_reader:
                if line[1] == "MSG IGNORED":
                    ignored_incorrect_response = True 
                    
                    msg = int(line[2])
                    msg_follower = msg % int(1e4)
                    msg_action = msg // int(1e10)
                    
                    if msg_action == 5 and msg_follower == self.extra.thisDevice.id:
                        received_incorrect_response = True
                        
            self.assertTrue(received_incorrect_response, "Leader did not receive the incorrect follower response")
            self.assertTrue(ignored_incorrect_response, "Leader did not ignore the incorrect follower response")
            
    def test_leader_assigns_deleted_devices_task_to_new_follower(self):
        """
        Establish that a leader device sends the task of a deleted device to a new follower 
        who joins (given that there are no reserves in the group).

        Returns
        -------
        None.

        """
        self.leader.set_process(self.leader.thisDevice.device_main)
        self.leader.start()
        time.sleep(3)
        self.follower.set_process(self.follower.thisDevice.device_main)
        self.follower.start()
        time.sleep(3)
        self.follower.stop()
        time.sleep(10)
        self.extra.set_process(self.extra.thisDevice.check_in_test_delete_from_wrong_follower)
        self.extra.start()
        time.sleep(5)
        self.leader.stop()
        self.extra.stop()
        
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)

            # conditions to see in logs
            dropped_follower = False
            picked_up_extra = False
            assigned_corr_task = False

            for line in leader_reader:
                if line[1] == "MSG SEND":
                    msg = int(line[2])
                    msg_action = msg // int(1e10)
                    msg_follower = msg % int(1e4)
                    msg_task = msg % int(1e10) // int(1e8)
                    
                    if msg_action == Action.DELETE.value:
                        dropped_follower = True
                    if dropped_follower and msg_action == Action.D_LIST.value and msg_follower == self.extra.thisDevice.id:
                        picked_up_extra = True
                        if msg_task == 2:
                            assigned_corr_task = True
                            
            # check all conditions met
            self.assertTrue(dropped_follower, "Tasks not assigned in sequential order")
            self.assertTrue(picked_up_extra, "Reserves not assigned task")
            self.assertTrue(assigned_corr_task, "Leader did not assign task from dropped device")
    
    def test_leader_assigns_deleted_devices_task_to_reserve(self):
        """
        Establish that a leader device sends the task of a deleted device to a reserve if
        one is available. 
        
        Returns
        -------
        None.

        """
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
        
        # start all devices
        self.leader.start()
        time.sleep(5)
        for m in range(9):
            nodes[m].start()
            time.sleep(3)
            
        # stop a non-reserve
        nodes[0].stop()
        time.sleep(10)
            
        # stop all devices
        self.leader.stop()
        for n in range(1,9):
            nodes[n].stop()
            
        with open(self.leader_file_name) as leader_logs:
            leader_reader = csv.reader(leader_logs)

            # conditions to see in logs
            dropped_follower = False
            assigned_task_to_reserve = False

            for line in leader_reader:
                if line[1] == "MSG SEND":
                    msg = int(line[2])
                    msg_action = msg // int(1e10)
                    msg_follower = msg % int(1e4)
                    msg_task = msg % int(1e10) // int(1e8)
                    
                    if msg_action == Action.DELETE.value:
                        dropped_follower = True
                    if dropped_follower and msg_action == Action.D_LIST.value and msg_follower == nodes[8].thisDevice.id:
                        if msg_task == 2:
                            assigned_task_to_reserve = True
                            
            # check all conditions met
            self.assertTrue(dropped_follower, "Tasks not assigned in sequential order")
            self.assertTrue(assigned_task_to_reserve, "Leader did not assign task from dropped device")
        
    
if __name__ == '__main__':
    unittest.main()

    
import unittest
import time
from simulation_network import SimulationNode, Network, PROVEN_MAX_WAIT_TIME
from message_classes import Action
import csv

class test_setup_protocol(unittest.TestCase):
    
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

    def test_follower_after_receiving_attendance(self):
        """
        Establish that a device using the main protocol becomes a follower after
        receiving an attendance message.

        Returns
        -------
        None.

        """
        
        # send leader process to attendance only 
        self.leader.set_process(self.leader.thisDevice.test_setup_leader_only_sends_attendance)
        # start leader
        self.leader.start()
        # start follower - send to device main
        self.follower.set_process(self.follower.thisDevice.device_main)
        self.follower.start()
        # wait ~3 seconds for follower to exit
        time.sleep(4)
        # stop both devices
        self.leader.stop()
        self.follower.stop()

        # check follower logs to confirm correct behavior
        with open(self.follower_file_name) as follower_logs:
            follower_reader = csv.reader(follower_logs)

            # conditions to see in logs
            corr_leader_rcvd = False
            received_att = False
            corr_behavior = False

            for line in follower_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_leader = msg % int(1e8) // int(1e4)
                    msg_action = msg // int(1e10)
                    if msg_leader == self.leader.thisDevice.id:
                        corr_leader_rcvd = True
                    if msg_action == Action.ATTENDANCE.value:
                        received_att = True
                if line[1] == "STATUS":
                    if line[2] == "BECOMING FOLLOWER":
                        corr_behavior = True

            # check all conditions met
            self.assertTrue(corr_leader_rcvd, "Correct leader never heard")
            self.assertTrue(received_att, "Never heard attendance")
            self.assertTrue(corr_behavior, "Did not become follower after hearing 1 attendance message")
            
    def test_follower_after_receiving_att_response(self):
        """
        Establish that device following the main protocol will recognize a group 
        has been formed after hearing an attendance response and wait for an attendance 
        message from leader.

        Returns
        -------
        None.

        """
        # send leader process to att response
        self.leader.set_process(self.leader.thisDevice.test_setup_leader_send_attendance_after_att_response)
        # send extra process to att response
        self.extra.set_process(self.extra.thisDevice.test_setup_follower_send_att_response)
        # send follower to main
        self.follower.set_process(self.follower.thisDevice.device_main)

        self.leader.start()
        self.extra.start()
        self.follower.start()

        time.sleep(4)

        self.leader.stop()
        self.extra.stop()
        self.follower.stop()

        # check follower logs to confirm correct behavior
        with open(self.follower_file_name) as follower_logs:
            follower_reader = csv.reader(follower_logs)

            # conditions to see in logs
            received_att_response = False
            received_attendance = False
            received_attendance_after_att_response = False
            corr_behavior = False

            for line in follower_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_action = msg // int(1e10)
                    if msg_action == Action.ATTENDANCE.value:
                        if received_att_response:
                            received_attendance_after_att_response = True
                        received_attendance = True
                    if msg_action == Action.ATT_RESPONSE.value:
                        received_att_response = True
                if line[1] == "STATUS":
                    if line[2] == "BECOMING FOLLOWER":
                        corr_behavior = True

            # check all conditions met
            self.assertTrue(received_att_response, "Device never heard attendance response")
            self.assertTrue(received_attendance, "Device never heard attendance")
            self.assertTrue(received_attendance_after_att_response , "Device heard attendance before attendance response")
            self.assertTrue(corr_behavior, "Device did not become follower after hearing 1 att_response and 1 attendance message")

    def test_follower_after_receiving_d_list(self):
        """
        Establish that device following the main protocol will recognize a group 
        has been formed after hearing a d_list message and wait for an attendance 
        message from leader.
        

        Returns
        -------
        None.

        """
        
        # send leader process to d_list
        self.leader.set_process(self.leader.thisDevice.test_setup_leader_send_two_d_list)
        # send follower to main
        self.follower.set_process(self.follower.thisDevice.device_main)

        self.leader.start()
        self.follower.start()

        time.sleep(4)

        self.leader.stop()
        self.follower.stop()

        # check follower logs to confirm correct behavior
        with open(self.follower_file_name) as follower_logs:
            follower_reader = csv.reader(follower_logs)

            # conditions to see in logs
            received_d_list = False
            received_attendance = False
            received_attendance_after_d_list = False
            corr_behavior = False

            for line in follower_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_action = msg // int(1e10)
                    if msg_action == Action.ATTENDANCE.value:
                        if received_d_list:
                            received_attendance_after_d_list = True
                        received_attendance = True
                    if msg_action == Action.D_LIST.value:
                        received_d_list = True
                if line[1] == "STATUS":
                    if line[2] == "BECOMING FOLLOWER":
                        corr_behavior = True

            # check all conditions met
            self.assertTrue(received_d_list, "Device never heard d_list")
            self.assertTrue(received_attendance, "Device never heard attendance")
            self.assertTrue(received_attendance_after_d_list, "Device heard attendance before d_list")
            self.assertTrue(corr_behavior, "Device did not become follower after hearing 1 d_list and 1 attendance message")

    def test_follower_after_receiving_check_in(self):
        """
        Establish that device following the main protocol will recognize a group 
        has been formed after hearing a check in message and wait for an attendance 
        message from leader.
        

        Returns
        -------
        None.

        """
        # send leader process to check in
        self.leader.set_process(self.leader.thisDevice.test_setup_leader_send_check_in)
        # send follower to main
        self.follower.set_process(self.follower.thisDevice.device_main)

        self.leader.start()
        self.follower.start()

        time.sleep(4)

        self.leader.stop()
        self.follower.stop()

        # check follower logs to confirm correct behavior
        with open(self.follower_file_name) as follower_logs:
            follower_reader = csv.reader(follower_logs)

            # conditions to see in logs
            received_check_in = False
            received_attendance = False
            received_attendance_after_check_in = False
            corr_behavior = False

            for line in follower_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_action = msg // int(1e10)
                    if msg_action == Action.ATTENDANCE.value:
                        if received_check_in:
                            received_attendance_after_check_in = True
                        received_attendance = True
                    if msg_action == Action.CHECK_IN.value:
                        received_check_in = True
                if line[1] == "STATUS":
                    if line[2] == "BECOMING FOLLOWER":
                        corr_behavior = True

            # check all conditions met
            self.assertTrue(received_check_in, "Device never heard check_in")
            self.assertTrue(received_attendance, "Device never heard attendance")
            self.assertTrue(received_attendance_after_check_in, "Device heard attendance before check in")
            self.assertTrue(corr_behavior, "Device did not become follower after hearing 1 check in and 1 attendance message")

    def test_follower_after_receiving_delete(self):
        """
        Establish that device following the main protocol will recognize a group 
        has been formed after hearing a delete message and wait for an attendance 
        message from leader.
        

        Returns
        -------
        None.

        """
        # send leader process to delete
        self.leader.set_process(self.leader.thisDevice.test_setup_leader_send_delete)
        # send follower to main
        self.follower.set_process(self.follower.thisDevice.device_main)

        self.leader.start()
        self.follower.start()

        time.sleep(4)

        self.leader.stop()
        self.follower.stop()

        # check follower logs to confirm correct behavior
        with open(self.follower_file_name) as follower_logs:
            follower_reader = csv.reader(follower_logs)

            # conditions to see in logs
            received_delete = False
            received_attendance = False
            received_attendance_after_delete = False
            corr_behavior = False

            for line in follower_reader:
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_action = msg // int(1e10)
                    if msg_action == Action.ATTENDANCE.value:
                        if received_delete:
                            received_attendance_after_delete = True
                        received_attendance = True
                    if msg_action == Action.DELETE.value:
                        received_delete = True
                if line[1] == "STATUS":
                    if line[2] == "BECOMING FOLLOWER":
                        corr_behavior = True

            # check all conditions met
            self.assertTrue(received_delete, "Device never heard d_list")
            self.assertTrue(received_attendance, "Device never heard attendance")
            self.assertTrue(received_attendance_after_delete, "Device heard attendance before d_list")
            self.assertTrue(corr_behavior, "Device did not become follower after hearing 1 d_list and 1 attendance message")

    # TODO: add tests for the other action codes

    def test_follower_after_maximum_wait_time(self):
        """
        Establish that the device will become a follower after waiting for the 
        mathematically proven maximum wait time for a message.
        

        Returns
        -------
        None.

        """
        # send leader process to wait
        self.leader.set_process(self.leader.thisDevice.test_setup_leader_wait_max_time)
        # send follower to main
        self.follower.set_process(self.follower.thisDevice.device_main)

        self.leader.start()
        self.follower.start()

        time.sleep(10)

        self.leader.stop()
        self.follower.stop()
        
        # check follower logs to confirm correct behavior
        with open(self.follower_file_name) as follower_logs:
            follower_reader = csv.reader(follower_logs)

            # conditions to see in logs
            wait_time = -1
            corr_behavior = False

            for line in follower_reader:
                if line[1] == "STATUS":
                    if line[2] == "STARTED DEVICE":
                        start_time = float(line[0])
                    if line[2] == "BECOMING FOLLOWER":
                        corr_behavior = True
                if line[1] == "MSG RCVD":
                    msg = int(line[2])
                    msg_action = msg // int(1e10)
                    if msg_action == Action.ATTENDANCE.value:
                        wait_time = float(line[0]) - start_time
                        
        self.assertNotEqual(wait_time, -1, "Device never received attendance")
        self.assertGreaterThan(wait_time, PROVEN_MAX_WAIT_TIME, "Device did not wait the max wait time")
        self.assertTrue(corr_behavior, "Device did not become follower after waiting max time for attendance")

if __name__ == '__main__':
    unittest.main()

    
import time
from message_classes import Message, Action
from abstract_network import AbstractTransceiver
from typing import Dict, List, Set
from pathlib import Path
import csv


CURRENT_FILE = Path(__file__).absolute()
PROTOCOL_DIR = CURRENT_FILE.parent
OUTPUT_DIR = PROTOCOL_DIR / "output"

MISSED_THRESHOLD: int = 2
RESPONSE_ALLOWANCE: float = 1  # subject to change
PRECISION_ALLOWANCE: int = 5
RECEIVE_TIMEOUT: float = 0.2
ATTENDANCE_DURATION: float = 2
D_LIST_DURATION: float = 2
DELETE_DURATION: float = 2


class Device:
    """ Lightweight device object for storing in a DeviceList. """

    def __init__(self, id):  # id will be generated by ThisDevice before attendance response
        """
        Non-default constructor for Device object.
        :param id: specified identifier for instance.
        """
        self.id: int = id  # unique device identifier, randomly generated
        self.leader: bool = False  # initialized as follower
        self.received: int | None = None  # holds most recent message payload
        self.missed: int = 0  # number of missed check-ins, used by current leader
        self.task: int = 0  # task identifier, 0 denotes reserve

    def get_id(self) -> int:
        """
        :return: Device's identifier.
        """
        return self.id

    def get_leader(self) -> bool:
        """
        :return: Device's current leader status.
        """
        return self.leader

    def get_received(self) -> int:
        """
        :return: Device's most recently received message.
        """
        return self.received

    def get_missed(self) -> int:
        """
        :return: number of missed check-ins for this Device.
        """
        return self.missed

    def reset_missed(self):
        self.missed = 0

    def get_task(self) -> int:
        """
        :return: device's current task identifier
        """
        return self.task

    def make_leader(self):
        """
        Makes this Device a leader
        """
        self.leader = True

    def make_follower(self):
        """
        Makes this Device a follower
        """
        self.leader = False

    def incr_missed(self) -> int:
        """
        Increments number of missed check-ins by 1.
        :return: new number of missed check-ins.
        """
        self.missed += 1
        return self.missed

    def set_task(self, task: int):
        """
        Sets the task for this Device.
        :param task: task's int identifier
        """
        self.task = task


class ThisDevice(Device):
    """ Object for main protocol to use, subclass of Device. """

    def __init__(self, id, transceiver: AbstractTransceiver):  # inclusive bounds
        """
        Constructor (default/non-default) for ThisDevice, creates additional fields.
        :param id: identifier for ThisDevice, either pre-specified or randomly generated.
        """
        super().__init__(id)
        self.leader: bool = True  # start ThisDevice as leader then change accordingly in setup
        self.device_list: DeviceList = DeviceList()  # default sizing
        self.leader_id: int | None = None
        self.leader_started_operating: float | None = None
        self.task_folder_idx: int | None = None  # multiple operations can be preloaded
        self.received: int | None = None  # will be an int representation of message
        self.transceiver: AbstractTransceiver = transceiver  # plugin object for sending and receiving messages
        self.numHeardDLIST: int = 0
        self.outPath = OUTPUT_DIR / ("device_log_" + str(self.id) + ".csv")
        self.active = True

    def send(self, action: int, payload: int, leader_id: int, follower_id: int, duration: float = 0.0):
        """
        Generates message with given parameters and sends to entire channel through transceiver.
        :param action: action
        :param payload: payload
        :param leader_id: leader_id
        :param follower_id: follower_id
        :param duration: sending duration in seconds
        """
        msg = Message(action, payload, leader_id, follower_id).msg

        # single-send with assumed perfect channel
        # users take responsibility of implementing duration send where needed
        self.transceiver.send(msg)  # transceiver only deals with integers
        self.log_message(msg, 'SEND')

    def receive(self, duration, action_value=-1) -> bool:  # action_value=-1 means accepts any action
        """
        Gets first message heard from transceiver with specified action,
        or any action if -1. Places integer message into self.received.
        :param duration: listening duration in seconds
        :param action_value: action value to listen for
        :return: True if valid message heard, False otherwise
        """
        # must have low timeout and larger duration so we don't get hung up on a channel
        end_time = time.time() + duration
        while time.time() < end_time:
            self.received = self.transceiver.receive(timeout=RECEIVE_TIMEOUT)
            if self.received == Message.DEACTIVATE:
                print("Device got deactivated by user")
                self.active = False
                self.make_follower()  # essentially wipe data
                self.device_list = DeviceList()  # TODO: make this helper
                return False
            if self.received == Message.ACTIVATE:
                print("Device got reactivated by user")
                self.active = True
                return False  # wait for next cycle, prevents interpreting injection as device
            # if a new leader is recognized, move into tiebreak scenario
            if self.received and self.leader_id and self.received_leader_id() != self.leader_id:  # another follower out there
                print(self.received_leader_id(), self.leader_id)
                self.handle_tiebreaker(self.received_leader_id())
                break
            if self.received and (action_value == -1 or self.received_action() == action_value):
                self.log_message(self.received, 'RCVD')
                return True
        return False

    def received_action(self) -> int:
        """
        :return: action bit of last received message
        :raise: ValueError if no message was received
        """
        if not self.received:
            raise ValueError("No message was received")
        return self.received // int(1e10)

    def received_leader_id(self) -> int:
        """
        :return: leader id of last received message
        :raise: ValueError if no message was received
        """
        if not self.received:
            raise ValueError("No message was received")
        return self.received % int(1e8) // int(1e4)

    def received_follower_id(self) -> int:
        """
        :return: follower id of last received message
        :raise: ValueError if no message was received
        """
        if not self.received:
            raise ValueError("No message was received")
        return self.received % int(1e4)

    def received_payload(self) -> int:
        """
        :return: payload of last received message
        :raise: ValueError if no message was received
        """
        if not self.received:
            raise ValueError("No message was received")
        return self.received % int(1e10) // int(1e8)

    def setup(self):
        """
        Startup sequence for ThisDevice. Listens to channel for existing leader.
        Assumes follower if heard, assumes leader otherwise.
        :return: None
        """
        print("Listening for leader's attendance")
        if self.receive(duration=3):
            print("Heard someone, listening for attendance")
            while not self.receive(duration=3, action_value=Action.ATTENDANCE.value):
                # print("Device", self.id, "is STUCK")
                pass
            self.make_follower()
            self.follower_handle_attendance()
            print("Leader was heard, becoming follower")
            return  # early exit if follower

        print("Assuming position of leader")
        self.make_leader()
        self.leader_id = self.id
        self.device_list.add_device(id=self.id, task=1)  # put itself in devicelist with first task
        self.leader_send_attendance()

    def leader_send_attendance(self):
        """
        Sending and receiving attendance sequence for leader. Updates and
        broadcasts device list if new device is heard.
        """
        print("Leader sending attendance")
        self.log_status("SENDING ATTENDANCE")
        self.send(action=Action.ATTENDANCE.value, payload=0, leader_id=self.id, follower_id=0, duration=ATTENDANCE_DURATION)

        # prevents deadlock
        while self.receive(duration=ATTENDANCE_DURATION*2, action_value=Action.ATT_RESPONSE.value):
            print("Leader heard attendance response from", self.received_follower_id())
            self.log_status("HEARD ATT_RESP FROM " + str(self.received_follower_id()))
            if self.received_follower_id() not in self.device_list.get_ids():
                unused_tasks = self.device_list.unused_tasks()
                print("Unused tasks: ", unused_tasks)
                self.log_status("UNUSED TASKS: " + str(unused_tasks))
                task = unused_tasks[0] if unused_tasks else 0
                print("Leader picked up device", self.received_follower_id())
                self.log_status("PICKED UP DEVICE " + str(self.received_follower_id()))
                self.device_list.add_device(id=self.received_follower_id(), task=task)  # has not assigned task yet

    def leader_send_device_list(self):
        """
        Helper to leader_send_attendance. Broadcasts message for each new device in network.
        :return:
        """
        for id, device in self.device_list.get_device_list().items():
            # not using option since DeviceList.devices is a dictionary
            # simply sending all id's in its "list" in follower_id position
            print("Leader sending D_LIST", id, device.task)
            self.send(action=Action.D_LIST.value, payload=device.task, leader_id=self.id, follower_id=id, duration=D_LIST_DURATION)

    # TODO: maybe handle leader collisions/tiebreakers here
    def leader_perform_check_in(self):
        """
        Leader executes check-in sequence for each follower in device_list. Updates
        number of missed check-ins if a device does not respond in time.
        :return:
        """
        # leader should listen for check-in response before moving on to ensure scalability
        for id, device in self.device_list.get_device_list().items():

            if id == self.id:
                continue

            got_response: bool = False
            # sending check-in to individual device
            print("Leader sending check-in to", id)
            self.log_status("SENDING CHECKIN TO " + str(id))
            self.send(action=Action.CHECK_IN.value, payload=0, leader_id=self.id, follower_id=id, duration=2)
            # device hangs in send() until finished sending
            end_time = time.time() + RESPONSE_ALLOWANCE
            # accounts for leader receiving another device's check-in response (which should never happen)
            while time.time() < end_time:  # times should line up with receive duration
                if self.receive(duration=RESPONSE_ALLOWANCE, action_value=Action.CHECK_IN.value):
                    # if tiebreak occurred during receive and no longer leader, end check in
                    if not self.get_leader():
                        return
                    
                    if abs(self.received_follower_id() - id) < PRECISION_ALLOWANCE:  # received message is same as sent message
                        # early exit if heard
                        got_response = True
                        print("Leader heard check-in response from", id)
                        self.log_status("HEARD CHECKIN RESPONSE FROM " + str(id))
                        break
            if got_response:
                device.reset_missed()
            else:
                device.incr_missed()

    def leader_drop_disconnected(self):
        """
        Leader checks for any disconnected devices. If found, updates
        device list and broadcasts delete message to all followers.
        """
        for id, device in self.device_list.get_device_list().copy().items():  # prevents modifying during iteration
            if device.get_missed() > MISSED_THRESHOLD:
                self.device_list.remove_device(id=id)  # remove from own list
                # sends a message for each disconnected device
                print("Leader sending DELETE message")
                self.log_status("SENDING DELETE")
                self.send(action=Action.DELETE.value, payload=0, leader_id=self.id, follower_id=id, duration=DELETE_DURATION)
                # broadcasts to entire channel, does not need a response confirmation

    def follower_handle_attendance(self):
        """
        Called after follower has received attendance message and assigned to self.received.
        """
        print("Follower", self.id, "handling attendance")
        self.log_status("HANDLING ATTENDANCE")
        self.leader_id = self.received_leader_id()
        # preconditions handled - always send response
        time.sleep(ATTENDANCE_DURATION/2)
        self.send(action=Action.ATT_RESPONSE.value, payload=0, leader_id=self.leader_id, follower_id=self.id, duration=ATTENDANCE_DURATION)

    def follower_respond_check_in(self):
        """
        Called after follower has received check-in message. Responds with same message.
        """
        print("Follower responding to check-in")
        self.log_status("RESPONDING TO CHECKIN")
        self.send(action=Action.CHECK_IN.value, payload=0, leader_id=self.leader_id, follower_id=self.id, duration=2)
        # sending and receiving is along different channels for Transceiver, so this should not be a problem

    def follower_handle_dlist(self):
        """
        Called after follower receives D_LIST action from leader. Updates device list.
        """
        print("Follower handling D_LIST")
        self.log_status("HANDLING DLIST")

        # handle already received device from original message
        # only add devices which are not already in device list
        # if self.received_follower_id() not in self.device_list.get_ids():
        self.log_status("ADDING " + str(self.received_follower_id()) + " TO DLIST")
        self.device_list.add_device(id=self.received_follower_id(), task=self.received_payload())

        # handle the rest of the list
        while self.receive(duration=0.5, action_value=Action.D_LIST.value):  # while still receiving D_LIST
            # only add new devices
            #if self.received_follower_id() not in self.device_list.get_ids():
            self.log_status("ADDING " + str(self.received_follower_id()) + " TO DLIST")
            self.device_list.add_device(id=self.received_follower_id(), task=self.received_payload())

    def follower_drop_disconnected(self):
        """
        Called after follower receives DELETE action from leader. Drops device from device list.
        :return:
        """
        self.device_list.remove_device(id=self.received_follower_id())
    
    def handle_tiebreaker(self, otherLeader : int):
        """
        Called if any device hears a leader other than the leader it has been following. 
        :return:
        """
        print("Tiebreaker hit by device ", self.id)
        self.log_status("HEARD OTHER LEADER: " + str(otherLeader))

        # if current leader has lower id than other leader, make the other leader the absolute leader
        if self.leader_id < otherLeader:
            # if leader, become follower
            if self.leader:
                self.make_follower()
                self.log_status("BECAME FOLLOWER")
                self.leader_id = otherLeader
            # if follower, recognize new leader
            else:
                self.leader_id = otherLeader
                self.log_status("NEW LEADER: " + str(otherLeader))
        # if current leader remains the same, add the other leader as a follower
        else:
            if self.leader and (otherLeader not in self.device_list.get_ids()):
                unused_tasks = self.device_list.unused_tasks()
                print("Unused tasks: ", unused_tasks)
                task = unused_tasks[0] if unused_tasks else 0
                print("Leader picked up device", otherLeader)
                self.device_list.add_device(id=otherLeader, task=task)  # has not assigned task yet

    def log_message(self, msg: int, direction: str):
        self.csvWriter.writerow([str(time.time()), 'MSG ' + direction, str(msg)])
        self.file.flush()

    def log_status(self, status: str):
        self.csvWriter.writerow([str(time.time()), 'STATUS', status])
        self.file.flush()

    # TODO: print log to individual files
    def device_main(self):
        """
        Main looping protocol for ThisDevice.
        """
        with self.outPath.open("w", encoding="utf-8", newline='') as self.file:
            # format is TIME, TYPE (STATUS, SENT, RECEIVED), CONTENT (<MSG>, <STATUS UPDATE>)
            self.csvWriter = csv.writer(self.file, dialect='excel')
            
            print("Starting main on device " + str(self.id))
            # create device object
            self.setup()

            if self.get_leader():
                print("--------Leader---------")
                self.log_status("BECAME LEADER")
            else:
                print("--------Follower, listening--------")
                self.log_status("BECAME FOLLOWER")
            while True:
                # global looping
                while self.active:
                    if self.get_leader():
                        print("Device:", self.id, self.leader, "\n", self.device_list)
                        self.leader_send_attendance()

                        # after receiving in attendance, make sure still leader
                        if not self.get_leader():
                            continue

                        self.leader_send_device_list()

                        time.sleep(2)

                        # will be helpful if leader works through followers in
                        # same order each time to increase clock speed
                        self.leader_perform_check_in()  # takes care of sending and receiving

                        # after receiving in check in, make sure still leader
                        if not self.get_leader():
                            continue

                        time.sleep(2)

                        self.leader_drop_disconnected()

                        time.sleep(2)

                        self.transceiver.clear()

                    if not self.get_leader():
                        # print("Device:", self.id, self.leader, "\n", self.device_list)
                        if not self.receive(duration=15):
                            print("Is there anybody out there?")
                            self.make_leader()
                            continue
                        elif abs(self.received_leader_id() - self.leader_id) > PRECISION_ALLOWANCE:  # account for loss of precision
                            # print(self.received_leader_id())
                            # print(self.leader_id)
                            # print("CONTINUE")
                            continue  # message was not from this device's leader - ignore

                        action = self.received_action()
                        # print(action)

                        # messages for all followers
                        match action:
                            case Action.ATTENDANCE.value:
                                # prevents deadlock between leader-follower first attendance state
                                if self.numHeardDLIST > 1 and self.device_list.find_device(self.id) is None:  # O(1) operation, quick
                                    self.follower_handle_attendance()
                                    self.numHeardDLIST = 0
                            case Action.CHECK_IN.value:
                                if abs(self.received_follower_id() - self.id) < PRECISION_ALLOWANCE:  # check-in directed to this device
                                    print("Follower", self.id, "heard directed check-in")
                                    self.follower_respond_check_in()
                                else:
                                    continue  # not necessary?
                            case Action.DELETE.value:
                                self.follower_drop_disconnected()  # even if self is wrongly deleted
                                # that will be handled later in Action.ATTENDANCE.value
                            case Action.D_LIST.value:
                                self.follower_handle_dlist()
                                self.numHeardDLIST += 1
                            case Action.TASK_STOP.value:
                                pass
                            case Action.TASK_START.value:
                                pass
                            case _:
                                pass

                            # probably do not need to clear follower channel
                            # self.transceiver.clear()
                while not self.active:
                    self.receive(duration=2)  # waiting for reactivation
                    time.sleep(2)  # can slow down clock speed here
                    # TODO: more formal dynamic clock
                


class DeviceList:
    """ Container for lightweight Device objects, held by ThisDevice. """

    def __init__(self, num_tasks=8):
        """
        Non-default constructor for DeviceList object.
        :param num_tasks: size of DeviceList, number of tasks.
        """
        self.devices = {}  # hashmap of id: Device object
        self.task_options = list(range(1, num_tasks+1))  # 1, 2, 3, 4

    def __str__(self):
        """
        String representation of Devices in DeviceList.
        :return: concatenated string representation.
        """

        output = ["DeviceList:"]
        for id, device in self.devices.items():
            task = device.get_task() if device.get_task() != 0 else "Reserve"
            output.append(f"Device ID: {id}, Task: {task}")
        return "\n\t".join(output)

    def __iter__(self):
        """
        Iterator for Devices in DeviceList.
        :return: iterator object.
        """
        return iter(self.devices.items())  # dictionary iterator

    def __len__(self):
        """
        Length of Devices in DeviceList.
        :return: number of Devices in DeviceList as an int.
        """
        return len(self.devices)

    def get_device_list(self) -> Dict[int, Device]:
        """
        :return: dictionary of {id : Device}
        """
        return self.devices

    def get_ids(self) -> Set[int]:
        """
        :return: hashable set of device ids
        """
        return set(self.devices.keys())

    def get_devices(self) -> Set[Device]:
        """
        :return: hashable set of Device objects
        """
        return set(self.devices.values())

    def update_num_tasks(self, num_tasks: int):
        """
        Resize DeviceList, used to upscale or downscale tasks.
        :param num_tasks: number of tasks in new operation.
        """
        self.task_options = list(range(num_tasks))

    def add_device(self, id: int, task: int):
        """
        Creates Device object with id and task, stores in DeviceList.
        :param id: identifier for device, assigned to new Device object.
        :param task: task for device, assigned to new Device object.
        """
        device = Device(id)
        device.set_task(task)
        self.devices[id] = device

    def find_device(self, id: int) -> int | None:
        """
        Finds Device object with target id in DeviceList.
        :param id: identifier for target device.
        :return: Device object if found, None otherwise.
        """
        return self.devices[id] if id in self.devices.keys() else None

    def remove_device(self, id: int) -> bool:
        """
        Removes Device object with target id in DeviceList.
        :param id: identifier for target device
        :return: True if found and removed, False otherwise.
        """
        try:
            self.devices.pop(id)
            return True
        except KeyError:
            return False

    def unused_tasks(self) -> List[int]:
        """
        Gets list of tasks not currently assigned to a device.
        :return: list of unused task indices.
        """
        unused_tasks = self.task_options.copy()
        for d in self.devices.values():
            if d.get_task() != 0 and d.get_task() in unused_tasks:
                unused_tasks.remove(d.get_task())
        return list(unused_tasks)  # need to index

    def get_reserves(self) -> List[Device]:
        """
        Gets list of reserve devices (not currently assigned a task).
        :return: list of reserve devices.
        """
        reserves = []
        for d in self.devices:
            if d.get_task() == 0:
                reserves.append(d)
        return reserves

    def update_task(self, id: int, task: int):
        """
        Reassigns task to target device.
        :param id: identifier for target device.
        :param task: new task to be assigned to target.
        """
        self.devices[id].set_task(task)

    def get_highest_id(self) -> Device | None:
        """
        Gets Device with the largest id, used for leader takeover and tiebreaker.
        :return: Device object with the largest id
        """
        return self.devices[max(self.devices.keys())] if len(self.devices) > 0 else None


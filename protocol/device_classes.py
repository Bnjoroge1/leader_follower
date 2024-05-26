import random
import message_classes

class Device:
    """ Lightweight device object for storing in a DeviceList. """

    def __init__(self, id):  # id will be generated by ThisDevice before attendance response
        """
        Non-default constructor for Device object.
        :param id: specified identifier for instance.
        """
        self.id = id  # unique device identifier, randomly generated
        self.leader = False  # initialized as follower
        self.received = None  # holds most recent message payload
        self.missed = 0  # number of missed check-ins, used by current leader
        self.task = -1  # task identifier, -1 denotes reserve

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

    def __init__(self, id=random.randint(1, int(1e8))):  # inclusive bounds
        """
        Constructor (default/non-default) for ThisDevice, creates additional fields.
        :param id: identifier for ThisDevice, either pre-specified or randomly generated.
        """
        super().__init__(id)
        self.device_list = DeviceList()  # default sizing
        self.leader_id = None
        self.leader_started_operating = None
        self.task_folder_idx = None  # multiple operations can be preloaded

    def send(self, action, payload, option, leader_id, follower_id):
        msg = message_classes.Message(action, payload, option, leader_id, follower_id).msg
        """ Send message through whatever communication method """

    def receive(self):
        pass

    def setup(self):
        pass

    # TODO: Model communication channel first
    # TODO: leader send attendance

    # TODO: leader send device list

    # TODO: leader send check in

    # TODO: leader send delete

    # TODO: leader send task start

    # TODO: leader send task stop

    # TODO: follower receive attendance

    # TODO: follower receive device list

    # TODO: follower receive check in

    # TODO: follower receive delete

    # TODO: follower receive task start

    # TODO: follower receive task stop

    # TODO: add edge case takeover situations after

    


class DeviceList:
    """ Container for lightweight Device objects, held by ThisDevice. """

    def __init__(self, num_tasks=8):
        """
        Non-default constructor for DeviceList object.
        :param num_tasks: size of DeviceList, number of tasks.
        """
        self.devices = []
        self.task_options = list(range(num_tasks))

    def __str__(self):
        """
        String representation of Devices in DeviceList.
        :return: concatenated string representation.
        """

        output = ["DeviceList:"]
        for device in self.devices:
            task = device.get_task() if device.get_task() != -1 else "Reserve"
            output.append(f"Device ID: {hex(device.get_id())}, Task: {task}")
        return "\n\t".join(output)

    def __iter__(self):
        """
        Iterator for Devices in DeviceList.
        :return: iterator object.
        """
        return iter(self.devices)

    def __len__(self):
        """
        Length of Devices in DeviceList.
        :return: number of Devices in DeviceList as an int.
        """
        return len(self.devices)

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
        self.devices.append(device)

    def find_device(self, id: int) -> int or None:
        """
        Finds Device object with target id in DeviceList.
        :param id: identifier for target device.
        :return: Device object if found, None otherwise.
        """
        for device in self.devices:
            if device.get_id() == id:
                return device
        return None

    def remove_device(self, id: int) -> bool:
        """
        Removes Device object with target id in DeviceList.
        :param id: identifier for target device
        :return: True if found and removed, False otherwise.
        """

        device = self.find_device(id)
        if device:
            self.devices.remove(device)
            return True
        return False

    def unused_tasks(self) -> [int]:
        """
        Gets list of tasks not currently assigned to a device.
        :return: list of unused task indices.
        """
        unused_tasks = self.task_options.copy()
        for d in self.devices:
            if d.get_task() != -1 and d.get_task() in unused_tasks:
                unused_tasks.remove(d.get_task())
        return unused_tasks

    def get_reserves(self):
        """
        Gets list of reserve devices (not currently assigned a task).
        :return: list of reserve devices.
        """
        reserves = []
        for d in self.devices:
            if d.get_task() == -1:
                reserves.append(d)
        return reserves

    def update_task(self, id: int, task: int):
        """
        Reassigns task to target device.
        :param id: identifier for target device.
        :param task: new task to be assigned to target.
        """
        for device in self.devices:
            if device.get_id() == id:
                device.set_task(task)  # pass-by-reference enhanced for allows this?
        # TODO: Exceptions

    def get_highest_id(self) -> Device:
        """
        Gets Device with the largest id, used for leader takeover and tiebreaker.
        :return: Device object with the largest id
        """
        max_device = None
        max_id = 0
        for device in self.devices:
            if device.get_id() > max_id:
                max_id = device.get_id()
                max_device = device  # reference to max Device object
        return max_device


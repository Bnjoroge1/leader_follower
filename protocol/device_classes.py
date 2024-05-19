import random


class Device:
    """ Lightweight device object for storing in a DeviceList. """

    def __init__(self, id=random.randint(0, 2**31 - 1)):
        """
        Constructor for Device object (default/non-default).
        :param id: specified identifier for instance.
        """
        self.id = id  # unique device identifier, randomly generated
        self.leader = False  # initialized as follower
        self.starter = False  # starter/reserve status
        self.received = None  # holds most recent message payload
        self.missed = 0  # number of missed check-ins, used by current leader

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

    def get_starter(self):
        """
        :return: Device's starter/reserve status.
        """
        return self.starter

    def get_received(self) -> int:
        """
        :return: Device's most recently received message.
        """
        return self.received

    def get_missed(self) -> int:
        """
        :return: Number of missed check-ins for this Device.
        """
        return self.missed

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

    def make_starter(self):
        """
        Makes this Device a starter.
        """
        self.starter = True

    def make_reserve(self):
        """
        Makes this Device a reserve.
        :return:
        """
        self.starter = False

    def incr_missed(self) -> int:
        """
        Increments number of missed check-ins by 1.
        :return: New number of missed check-ins.
        """
        self.missed += 1
        return self.missed
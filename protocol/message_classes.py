from enum import Enum


class Message:
    """ Object carrying action, payload, option. """

    def __init__(self, action: int, payload: int, option: int, leader_id: int, follower_id: int):
        """
        Non-default constructor for Message object, MSD to LSD.
        :param action: indicator for type of message, 1 digit.
        :param payload: main message contents, 8 digits.
        :param option: extra message contents, 2 digits.
        :param leader_id: id of device's leader, itself if device is leader, 8 digits
        :param follower_id: id of device's follower, itself if device is follower, 8 digits
        """
        self.action = action
        self.payload = payload
        self.option = option
        self.leader_id = leader_id
        self.follower_id = follower_id
        self.msg = int((action * 1e26) + (payload * 1e18) + (option * 1e16) + (leader_id * 1e8) + (follower_id))

    def __str__(self) -> str:
        """
        String representation of Message object, used for console printing.
        :return: Concatenated string representation.
        """
        out = [
            f"message w/ Action: {self.action}",
            f"Leader Address: {hex(self.leader_id)}",
            f"Follower Address: {hex(self.follow_id)}",
            f"Options: {self.option}",
        ]
        return "\n\t".join(out)


class Action(Enum):
    ATTENDANCE = 1  # leader sends attendance to entire channel
    ATT_RESPONSE = 2  # untracked device responds to leader's attendance
    D_LIST = 3  # leader sends updated device list to entire channel
    CHECK_IN = 4  # leader sends personalized check-in to a tracked follower
    DELETE = 5  # leader sends delete message to entire channel
    NEW_LEADER = 6  # newly appointed leader sends to entire channel
    TASK_START = 7  # leader sends personalized message to a tracked follower
    TASK_STOP = 8  # leader sends personalized message to a tracked follower
    INFORMATION = 9  # any device sends information to channel TODO: implement database


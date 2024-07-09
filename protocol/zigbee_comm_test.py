import zigpy
from zigpy.zdo.types import LogicalType
from zigpy.zcl.clusters.general import OnOff

class RobotNode(AbstractNode):
    def __init__(self, name: str, transceiver: "RobotTransceiver"):
        super().__init__(name)
        self.transceiver = transceiver

    def send_message(self, message: str):
        self.transceiver.send(message)

    def receive_message(self):
        return self.transceiver.receive()

class RobotTransceiver(AbstractTransceiver):
    def __init__(self, zigbee_channel: int):
        super().__init__()
        self.zigbee_channel = zigbee_channel
        self.zigbee_network = None  

    def initialize_zigbee(self):
        # this should initialize zigbee network
        self.zigbee_network = zigpy.zigbee.api.zigbee_device(zigbee_channel=self.zigbee_channel)
        self.zigbee_network.startup()

        # set the node type based on whether it's the leader or follower --> testing purposes only
        if self.zigbee_network.is_coordinator:
            self.node_type = "Leader"
        else:
            self.node_type = "Follower"

    def send(self, message: str):
        self.zigbee_network.send_message(message)

    def receive(self):
        return self.zigbee_network.receive_message()

if __name__ == "__main__":
    # setup Zigbee transceivers and nodes
    leader_transceiver = RobotTransceiver(zigbee_channel=15)
    leader_node = RobotNode("Leader", leader_transceiver)

    follower1_transceiver = RobotTransceiver(zigbee_channel=15)
    follower1_node = RobotNode("Follower1", follower1_transceiver)

    follower2_transceiver = RobotTransceiver(zigbee_channel=15)
    follower2_node = RobotNode("Follower2", follower2_transceiver)

    follower3_transceiver = RobotTransceiver(zigbee_channel=15)
    follower3_node = RobotNode("Follower3", follower3_transceiver)

    # initialize Zigbee networks --> only testing with 4 modules for now
    leader_transceiver.initialize_zigbee()
    follower1_transceiver.initialize_zigbee()
    follower2_transceiver.initialize_zigbee()
    follower3_transceiver.initialize_zigbee()

    leader_node.send_message("Sending from leader: hi followers!")

    # message reception
    print(f"Follower1 received: {follower1_node.receive_message()}")
    print(f"Follower2 received: {follower2_node.receive_message()}")
    print(f"Follower3 received: {follower3_node.receive_message()}")

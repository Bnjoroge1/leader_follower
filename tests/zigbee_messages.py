
from protocol.robot_network import RobotNode, RobotTransceiver

# tester file for sending and recieving messages for specific transcievers
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
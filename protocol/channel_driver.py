import time
import network_classes as nc
import itertools


def main():
    """
    Main driver for protocol simulation.
    :return:
    """
    # startup
    num_devices = 3
    network = nc.Network()
    nodes = []
    for i in range(num_devices):
        new_node = nc.Node(i+1)
        nodes.append(new_node)
        network.add_node(new_node.node_id, new_node)

    for firstNode in nodes:
        for secondNode in nodes:
            if firstNode is not secondNode:
                print("CHANNEL SETUP", firstNode.node_id, secondNode.node_id)
                network.create_channel(firstNode.node_id, secondNode.node_id)

    for node in nodes:
        node.start()
        time.sleep(5)


if __name__ == "__main__":
    main()

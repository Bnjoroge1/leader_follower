import time
import simulation_network as sn
import itertools


def main():
    """
    Main driver for protocol simulation.
    :return:
    """
    # startup
    num_devices = 10
    network = sn.Network()
    nodes = []
    for i in range(num_devices):
        new_node = sn.Node(i+1)
        nodes.append(new_node)
        network.add_node(new_node.node_id, new_node)

    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            firstNode = nodes[i]
            secondNode = nodes[j]
            print("CHANNEL SETUP", firstNode.node_id, secondNode.node_id)
            network.create_channel(firstNode.node_id, secondNode.node_id)

    visualizer = sn.NetworkVisualizer()
    visualizer.ui_main()

    for node in nodes:
        node.start()
        time.sleep(5)


if __name__ == "__main__":
    main()

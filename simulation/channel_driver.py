import random
import threading
import time
import network_classes as nc
import sys
sys.path.append('../protocol')

def main():
    """
    Main driver for protocol simulation.
    :return:
    """
    # startup
    num_devices = 2
    # each ThisDevice is a field of a Node instance
    network = nc.NetworkVisualizer()
    nodes = list(range(num_devices))
    port = 6000
    for i in range(len(nodes)):
        print("Making node " + str(i))
        nodes[i] = nc.Node('localhost', port + i, 'Node' + str(i), network)

    threads = []
    # devices get set up in series but run in parallel (prevents accidental leaders)
    for node in nodes:
        print("Starting device " + str(node.__hash__()))
        node.thread.start()
        threads.append(node.thread)
        time.sleep(3)

    print(threads)

    # visualization
    network.visualize()

    for node in nodes:
        node.close()

# # Create a NetworkVisualizer instance
# network = nc.NetworkVisualizer()
#
# # Create nodes with the network visualizer
# node1 = nc.Node('localhost', 6000, 'Node1', network)
# node2 = nc.Node('localhost', 6001, 'Node2', network)
# node3 = nc.Node('localhost', 6002, 'Node3', network)
#
# # Wait for servers to start
# time.sleep(1)
#
# # Connect nodes to form a mesh
# node1.connect_to_neighbor('localhost', 6001, 'Node2')
# node1.connect_to_neighbor('localhost', 6002, 'Node3')
# node2.connect_to_neighbor('localhost', 6000, 'Node1')
# node2.connect_to_neighbor('localhost', 6002, 'Node3')
# node3.connect_to_neighbor('localhost', 6000, 'Node1')
# node3.connect_to_neighbor('localhost', 6001, 'Node2')
#
# # Send messages between nodes
# node1.send_message('localhost', 6001, 'Hello from Node1 to Node2')
# node2.send_message('localhost', 6002, 'Hello from Node2 to Node3')
# node3.send_message('localhost', 6000, 'Hello from Node3 to Node1')
#
# # Allow some time for messages to be received
# time.sleep(2)
#
# # Visualize the network
# network.visualize()
#
# # Close nodes
# node1.close()
# node2.close()
# node3.close()


if __name__ == "__main__":
    main()

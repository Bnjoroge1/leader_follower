import time
import network_classes as nc


# Create a NetworkVisualizer instance
network = nc.NetworkVisualizer()

# Create nodes with the network visualizer
node1 = nc.Node('localhost', 5000, 'Node1', network)
node2 = nc.Node('localhost', 5001, 'Node2', network)
node3 = nc.Node('localhost', 5002, 'Node3', network)

# Wait for servers to start
time.sleep(1)

# Connect nodes to form a mesh
node1.connect_to_neighbor('localhost', 5001, 'Node2')
node1.connect_to_neighbor('localhost', 5002, 'Node3')
node2.connect_to_neighbor('localhost', 5000, 'Node1')
node2.connect_to_neighbor('localhost', 5002, 'Node3')
node3.connect_to_neighbor('localhost', 5000, 'Node1')
node3.connect_to_neighbor('localhost', 5001, 'Node2')

# Send messages between nodes
node1.send_message('localhost', 5001, 'Hello from Node1 to Node2')
node2.send_message('localhost', 5002, 'Hello from Node2 to Node3')
node3.send_message('localhost', 5000, 'Hello from Node3 to Node1')

# Allow some time for messages to be received
time.sleep(2)

# Visualize the network
network.visualize()

# Close nodes
node1.close()
node2.close()
node3.close()

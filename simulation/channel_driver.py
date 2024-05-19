import network_classes as nc

num_devices = 8

# Create graph
mesh_network = nc.Graph(num_devices)

# Add nodes to the graph
for i in range(1, 4):
    mesh_network.add_node(i)

# Define edges (mesh network topology)
mesh_network.add_edge(1, 2)
mesh_network.add_edge(1, 3)
mesh_network.add_edge(2, 3)

# Create nodes with the graph reference
node1 = nc.Node(1, 5001, mesh_network)
node2 = nc.Node(2, 5002, mesh_network)
node3 = nc.Node(3, 5003, mesh_network)

# Start nodes
node1.start()
node2.start()
node3.start()

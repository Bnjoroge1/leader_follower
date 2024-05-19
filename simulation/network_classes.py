import socket
import threading


class Graph:
    """
    Dense graph representation of mesh network, uses adjacency matrix.
    """

    def __init__(self, size):
        self.size = size
        self.adjacency_matrix = [[0] * size for _ in range(size)]

    def add_node(self, node_id):
        # In an adjacency matrix, nodes are implicit in the matrix size
        # No need to explicitly add a node
        pass

    def add_edge(self, node1, node2):
        self.adjacency_matrix[node1 - 1][node2 - 1] = 1
        self.adjacency_matrix[node2 - 1][node1 - 1] = 1

    def get_neighbors(self, node_id):
        neighbors = []
        for idx, is_neighbor in enumerate(self.adjacency_matrix[node_id - 1]):
            if is_neighbor:
                neighbors.append(idx + 1)
        return neighbors


class Node:
    """
    Node class representing a device in the protocol.
    """

    def __init__(self, node_id, port, graph):
        self.node_id = node_id
        self.port = port
        self.graph = graph
        self.running = True

    def listen(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('localhost', self.port))
        while self.running:
            message, addr = s.recvfrom(1024)
            print(f"Node {self.node_id} received message: {message.decode()} from {addr}")
            self.handle_message(message.decode(), addr)

    def handle_message(self, message, addr):
        # Basic handling: just print out the message
        print(f"Node {self.node_id} processing message: {message}")

    def send_message(self, message, target_port):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(message.encode(), ('localhost', target_port))

    def broadcast(self, message):
        neighbors = self.graph.get_neighbors(self.node_id)
        for neighbor_id in neighbors:
            # Here we assume that the node_id maps directly to the port (e.g., node_id 1 -> port 5001)
            target_port = 5000 + neighbor_id
            self.send_message(message, target_port)

    def start(self):
        thread = threading.Thread(target=self.listen)
        thread.start()

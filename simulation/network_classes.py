import socket
import threading
import networkx as nx
import matplotlib.pyplot as plt
import sys
import random
sys.path.append('../protocol')
from protocol import device_classes as dc


class Node:
    def __init__(self, host, port, node_id, network):
        self.host = host
        self.port = port
        self.node_id = node_id
        self.network = network
        self.neighbors = {}
        # user takes responsibility of assigning ids
        self.thisDevice = dc.ThisDevice(self.__hash__())
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.thread = threading.Thread(target=self.thisDevice.device_main)
        self.network.add_node(self.node_id)  # Add the node to the network graph

    def listen_for_neighbors(self):
        print(f"Node {self.node_id} listening on {self.host}:{self.port}")
        while True:
            conn, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_neighbor, args=(conn, addr)).start()

    def handle_neighbor(self, conn, addr):
        print(f"Node {self.node_id} connected by {addr}")
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"Node {self.node_id} received: {data.decode()}")
            except:
                break
        conn.close()

    def connect_to_neighbor(self, neighbor_host, neighbor_port, neighbor_id):
        neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        neighbor_socket.connect((neighbor_host, neighbor_port))
        self.neighbors[(neighbor_host, neighbor_port)] = neighbor_socket
        self.network.add_edge(self.node_id, neighbor_id)  # Add the connection to the network graph

    def send_message(self, neighbor_host, neighbor_port, message):
        if (neighbor_host, neighbor_port) in self.neighbors:
            self.neighbors[(neighbor_host, neighbor_port)].sendall(message.encode())
        else:
            print(f"Neighbor {neighbor_host}:{neighbor_port} not found!")

    def close(self):
        for neighbor in self.neighbors.values():
            neighbor.close()
        self.server_socket.close()


class NetworkVisualizer:
    def __init__(self):
        self.graph = nx.Graph()

    def add_node(self, node_id):
        self.graph.add_node(node_id)

    def add_edge(self, node_id1, node_id2):
        self.graph.add_edge(node_id1, node_id2)

    def visualize(self):
        plt.figure(figsize=(10, 7))
        pos = nx.spring_layout(self.graph)
        nx.draw(self.graph, pos, with_labels=True, node_size=700, node_color="skyblue",
                font_size=15, font_color="black", font_weight="bold", edge_color="gray")
        plt.show()

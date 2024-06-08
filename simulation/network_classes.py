import sys
sys.path.append('../protocol')
from protocol import device_classes as dc
import multiprocessing
import queue as q


class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.transceiver = Transceiver()
        self.thisDevice = dc.ThisDevice(self.node_id, self.transceiver)
        self.process = multiprocessing.Process(target=self.thisDevice.device_main)

    def start(self):
        self.process.start()

    def stop(self):
        self.process.terminate()
        self.process.join()

    def set_channel(self, target_node_id, queue):
        self.transceiver.set_channel(target_node_id, queue)


class Network:
    def __init__(self):
        self.nodes = {}
        self.channels = {}

    def add_node(self, node_id, node):
        self.nodes[node_id] = node

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    def create_channel(self, node_id1, node_id2):  # bidirectional
        queue1 = multiprocessing.Queue()
        queue2 = multiprocessing.Queue()
        self.channels[(node_id1, node_id2)] = (queue1, queue2)
        self.channels[(node_id2, node_id1)] = (queue2, queue1)
        self.nodes[node_id1].set_channel(node_id2, queue1)
        self.nodes[node_id2].set_channel(node_id1, queue2)


# TODO: implement removing channels (node_ids) as devices get dropped from devicelist
# similar implementation to send/receive calling transceiver functions
class Transceiver:
    def __init__(self):
        self.channels = {}  # hashmap between node_id and Queue (channel)

    def set_channel(self, node_id, queue):
        self.channels[node_id] = queue

    def send(self, msg: int):  # send to all channels
        for queue in self.channels.values():
            if queue is not None:
                queue.put(msg)

    def receive(self, timeout: int) -> int | None:  # get from all queues
        # TODO: maybe change to received message list?
        # messages = []
        # for channel in self.channels.values():
        #     try:
        #         messages.append(channel.get(timeout=timeout))
        #     except queue.Empty:
        #         pass
        # return messages[0]
        for queue in self.channels.values():
            try:
                msg = queue.get(timeout=timeout)
                return msg
            except q.Empty:
                pass
        return None


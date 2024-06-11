import sys
import device_classes as dc
import multiprocessing
import queue as q


class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.transceiver = Transceiver()
        self.thisDevice = dc.ThisDevice(self.__hash__() % 100000000, self.transceiver)
        self.process = multiprocessing.Process(target=self.thisDevice.device_main)

    def start(self):
        self.process.start()

    def stop(self):
        self.process.terminate()
        self.process.join()

    def set_outgoing_channel(self, target_node_id, queue):
        self.transceiver.set_outgoing_channel(target_node_id, queue)

    def set_incoming_channel(self, target_node_id, queue):
        self.transceiver.set_incoming_channel(target_node_id, queue)


class Network:
    def __init__(self):
        self.nodes = {}
        # self.channels - add later

    def add_node(self, node_id, node):
        self.nodes[node_id] = node

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    def create_channel(self, node_id1, node_id2):  # 2 channels for bidirectional comms
        queue1 = multiprocessing.Queue()  # from 1 to 2
        queue2 = multiprocessing.Queue()  # from 2 to 1
        self.nodes[node_id1].set_outgoing_channel(node_id2, queue1)  # (other node, channel)
        self.nodes[node_id1].set_incoming_channel(node_id2, queue2)
        self.nodes[node_id2].set_outgoing_channel(node_id1, queue2)
        self.nodes[node_id2].set_incoming_channel(node_id2, queue1)


# TODO: implement removing channels (node_ids) as devices get dropped from devicelist
# similar implementation to send/receive calling transceiver functions
class Transceiver:
    def __init__(self):
        self.outgoing_channels = {}  # hashmap between node_id and Queue (channel)
        self.incoming_channels = {}

    def set_outgoing_channel(self, node_id, queue):
        self.outgoing_channels[node_id] = queue

    def set_incoming_channel(self, node_id, queue):
        self.incoming_channels[node_id] = queue

    def send(self, msg: int):  # send to all channels
        for queue in self.outgoing_channels.values():
            if queue is not None:
                queue.put(msg)

    def receive(self, timeout: float) -> int | None:  # get from all queues
        # TODO: maybe change to received message list?
        # messages = []
        # for channel in self.channels.values():
        #     try:
        #         messages.append(channel.get(timeout=timeout))
        #     except queue.Empty:
        #         pass
        # return messages[0]
        for queue in self.incoming_channels.values():
            try:
                msg = queue.get(timeout=timeout)
                return msg
            except q.Empty:
                pass
        return None


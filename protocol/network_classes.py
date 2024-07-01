import device_classes as dc
import multiprocessing
import queue as q
from typing import Dict, Union
from xbee import ZigBee
import serial
import time

class Node:
    def __init__(self, node_id, target_func=None, target_args=None):
        self.node_id = node_id
        self.transceiver = ZigbeeTransceiver()  # Use ZigbeeTransceiver here
        self.thisDevice = dc.ThisDevice(self.__hash__() % 10000, self.transceiver)
        # self.thisDevice = dc.ThisDevice(node_id*100, self.transceiver)  # used for repeatable testing
        # for testing purposes, so node can be tested without device protocol fully implemented
        # can be removed later
        if target_func is None:
            target_func = self.thisDevice.device_main
        if target_args is not None:
            target_args = (self.transceiver, self.node_id)
            self.process = multiprocessing.Process(target=target_func, args=target_args)
        else:
            self.process = multiprocessing.Process(target=target_func)

    def start(self):
        self.process.start()

    def stop(self):
        # terminate will kill process so I don't think we need to join after - this can corrupt shared data
        self.process.terminate()
        # self.process.join()

    def join(self):
        # not sure if needed for protocol, but was used during testing
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
        queue1 = ChannelQueue()  # from 1 to 2
        queue2 = ChannelQueue()  # from 2 to 1
        self.nodes[node_id1].set_outgoing_channel(node_id2, queue1)  # (other node, channel)
        self.nodes[node_id1].set_incoming_channel(node_id2, queue2)
        self.nodes[node_id2].set_outgoing_channel(node_id1, queue2)
        self.nodes[node_id2].set_incoming_channel(node_id1, queue1)


class NetworkVisualizer:
    def __init__(self):
        pass

    def ui_main(self):
        pass


class ChannelQueue:
    """
    Wrapper class for multiprocessing.Queue that keeps track of number of
    messages in channel and updates. Maintains thread safety.
    """
    def __init__(self):
        self.queue = multiprocessing.Queue()
        self.size = multiprocessing.Value('i', 0, lock=True)  # shared value with lock for size

    def put(self, msg):
        self.queue.put(msg)
        with self.size.get_lock():
            self.size.value += 1

    def get(self, timeout=None):
        msg = self.queue.get(timeout=timeout)
        with self.size.get_lock():
            self.size.value -= 1
        return msg

    def get_nowait(self):
        msg = self.queue.get_nowait()
        with self.size.get_lock():
            self.size.value -= 1
        return msg

    def get_size(self):
        with self.size.get_lock():
            return self.size.value

    def is_empty(self):
        with self.size.get_lock():
            return self.size.value == 0

    def empty(self):
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except q.Empty:
                break


class Transceiver:
    def __init__(self):
        self.outgoing_channels = {}  # hashmap between node_id and Queue (channel)
        self.incoming_channels = {}

    def set_outgoing_channel(self, node_id, queue: ChannelQueue):
        self.outgoing_channels[node_id] = queue

    def set_incoming_channel(self, node_id, queue: ChannelQueue):
        self.incoming_channels[node_id] = queue

    def send(self, msg: int):  # send to all channels
        for id, queue in self.outgoing_channels.items():
            if queue is not None:
                queue.put(msg)

    def receive(self, timeout: float) -> Union[int, None]:  # get from all queues
        for id, queue in self.incoming_channels.items():
            try:
                msg = queue.get(timeout=timeout)
                return msg
            except q.Empty:
                pass
        return None

    def clear(self):
        for queue in self.outgoing_channels.values():
            while not queue.is_empty():
                try:
                    queue.get_nowait()
                except q.Empty:
                    pass
        for queue in self.incoming_channels.values():
            while not queue.is_empty():
                try:
                    queue.get_nowait()
                except q.Empty:
                    pass


class ZigbeeTransceiver:
    def __init__(self, serial_port='/dev/ttyUSB0', baud_rate=9600):
        self.serial_port = serial.Serial(serial_port, baud_rate)
        self.xbee = ZigBee(self.serial_port)
        self.outgoing_channels = {}  # hashmap between node_id and Queue (channel)
        self.incoming_channels = q.Queue()

    def set_outgoing_channel(self, node_id, address):
        self.outgoing_channels[node_id] = address

    def send(self, msg: str):  # send to all channels
        for node_id, address in self.outgoing_channels.items():
            if address:
                self.xbee.send('tx', dest_addr=address, data=msg.encode())
                print(f"Message '{msg}' sent to device {node_id}")

    def receive(self, timeout: float) -> Union[str, None]:
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                response = self.xbee.wait_read_frame()
                msg = response.get('rf_data').decode()
                self.incoming_channels.put(msg)
                return msg
            except q.Empty:
                pass
            except Exception as e:
                print(f"Error receiving message: {e}")
        return None

    def clear(self):
        with self.incoming_channels.mutex:
            self.incoming_channels.queue.clear()
import device_classes as dc
import multiprocessing
import queue as q
from typing import Dict
from abstract_network import AbstractNode, AbstractTransceiver
import asyncio
import websockets
import threading
from message_classes import Message

class SimulationNode(AbstractNode):

    def __init__(self, node_id, target_func = None, target_args = None, active: multiprocessing.Value = None):
        self.node_id = node_id
        self.transceiver = SimulationTransceiver(parent=self, active=active)
        self.thisDevice = dc.ThisDevice(self.__hash__() % 10000, self.transceiver)
        # self.thisDevice = dc.ThisDevice(node_id*100, self.transceiver)  # used for repeatable testing
        # for testing purposes, so node can be tested without device protocol fully implemented
        # can be removed later
        if not target_func:
            target_func = self.thisDevice.device_main
        if target_args:
            target_args = (self.transceiver, self.node_id)
            self.process = multiprocessing.Process(target=target_func, args=target_args)
        else:
            self.process = multiprocessing.Process(target=target_func)

    async def async_init(self):  # SimulationTransceiver
        await self.transceiver.websocket_client()

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


# TODO: implement removing channels (node_ids) as devices get dropped from devicelist
# similar implementation to send/receive calling transceiver functions
class SimulationTransceiver(AbstractTransceiver):

    def __init__(self, parent: SimulationNode, active: multiprocessing.Value):
        self.outgoing_channels = {}  # hashmap between node_id and Queue (channel)
        self.incoming_channels = {}
        self.parent = parent
        self.active: multiprocessing.Value = active  # can activate or deactivate device with special message

    def deactivate(self):
        self.active.value = 0

    def reactivate(self):
        self.active.value = 1

    def stay_active(self):
        self.active.value = 2

    def active_status(self):
        return self.active.value

    def set_outgoing_channel(self, node_id, queue: ChannelQueue):
        self.outgoing_channels[node_id] = queue

    def set_incoming_channel(self, node_id, queue: ChannelQueue):
        self.incoming_channels[node_id] = queue

    def send(self, msg: int):  # send to all channels
        # if msg // int(1e10) == 2:
        #     print(msg)
        #     print(self.outgoing_channels.keys())
        for id, queue in self.outgoing_channels.items():
            if queue is not None:
                queue.put(msg)
                # print("msg", msg, "put in device", id)
        # no need to wait for this task to finish before returning to protocol
        asyncio.run(self.notify_server(f"SENT,{self.parent.node_id}"))

    def receive(self, timeout: float) -> int | None:  # get from all queues\
        if self.active_status() == 0:
            print("returning DEACTIVATE")
            return Message.DEACTIVATE
        if self.active_status() == 1:  # can change to Enum
            self.stay_active()
            return Message.ACTIVATE
        # print(self.incoming_channels.keys())
        for id, queue in self.incoming_channels.items():
            try:
                msg = queue.get(timeout=timeout)
                # print("Message", msg, "gotton from", id)
                asyncio.run(self.notify_server(f"RCVD,{self.parent.node_id}"))
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
    
    async def websocket_client(self):
        uri = "ws://localhost:3000"  # server.js websocket server
        async with websockets.connect(uri) as websocket:
            await websocket.send(f"CONNECTED,{self.parent.node_id}")

            async for message in websocket:
                if isinstance(message, bytes):
                    message = message.decode("utf-8")
                print(f"Received message: {message}")
                if message == "Toggle Device":
                    print("Toggling device")
                    if self.active_status() == 0:  # been off
                        self.reactivate()  # goes through process to full activation
                    else:
                        self.deactivate()  # recently just turned on

    async def notify_server(self, message: str):
        uri = "ws://localhost:3000"  # server.js websocket server
        async with websockets.connect(uri) as websocket:
            await websocket.send(message)
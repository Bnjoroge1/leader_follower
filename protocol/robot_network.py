import device_classes as dc
import multiprocessing
import queue as q
from typing import Dict
from abstract_network import AbstractNode, AbstractTransceiver

import zigpy
import asyncio
from collections import deque
import queue as q

class RobotNode(AbstractNode):
    def __init__(self, name: str, transceiver: "RobotTransceiver"):
        super().__init__(name)
        self.transceiver = transceiver

    def send_message(self, message: str):
        self.transceiver.send(message)

    def receive_message(self):
        return self.transceiver.receive()

class RobotTransceiver(AbstractTransceiver):
    def __init__(self, zigbee_channel: int, active: multiprocessing.Value):
        super().__init__()
        self.zigbee_channel = zigbee_channel
        self.active = active # used for device deactivation 
        self.logQ = deque()
        self.outgoing_channels = {}
        self.incoming_channels = {}


    def initialize_zigbee(self):
        # TODO: initialize zigbee network
        self.zigbee_network = zigpy.zigbee.api.zigbee_device(zigbee_channel=self.zigbee_channel)
        self.zigbee_network.startup()

    def send(self, message: str):
        # each message gets logged and then sent to network
        self.logQ.appendleft(message)
        print(f"Sending message: {message}")
        for queue in self.outgoing_channels.values():
            queue.put(message)

    def receive(self):
        # recieving messages from queue
        for queue in self.incoming_channels.values():
            try:
                msg = queue.get(timeout=0.1)
                print(f"Received message: {msg}")
                return msg
            except q.Empty:
                pass
        return ""
    
    def set_outgoing_channel(self, node_id, queue: q.Queue):
        self.outgoing_channels[node_id] = queue

    def set_incoming_channel(self, node_id, queue: q.Queue):
        self.incoming_channels[node_id] = queue

    def activate(self):
        self.active.value = 1

    def deactivate(self):
        self.active.value = 0

    def check_status(self):
        return self.active.value
    

def main():
    active = multiprocessing.Value('i', 1) # activate the transciever
    zigbee_channel = 15 # zigbee supposedly has channels 11-26, each corresponding to a specific 2.4GHz frequency for sending messages

    transceiver = RobotTransceiver(zigbee_channel=zigbee_channel, active=active)
    node = RobotNode(name="Robot", transceiver=transceiver) # ask dhilan and kayleigh if I need a separate node for each of the 5 robots?

    transceiver.initialize_zigbee()

    node.send_message("Test message")
    message = node.receive_message()

    print(f"Message Recieved: {message}")

    # ask dhilan and kayleigh if this method adheres to the synchronous heartbeats discussed?

if __name__ == "__main__":
    main()
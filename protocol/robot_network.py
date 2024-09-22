import device_classes as dc
import multiprocessing
import queue as q
from typing import Dict
from abstract_network import AbstractNode, AbstractTransceiver

import zigpy.application
from zigpy.device import Device

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

# notes from 9/16 meeting
# queue is not necessary
# subclass zigpy's send function with transciever --> review simulation_network to see how the simulated transciever sends messages
# use asyncio for sync messages that block main thread --> something along the lines of self.recieve wrapped in asyncio call
# outgoing and incoming channels not needed
# replace logging with print statements

class RobotTransceiver(AbstractTransceiver):
    def __init__(self, zigbee_channel: int, active: multiprocessing.Value):
        super().__init__()
        self.zigbee_channel = zigbee_channel
        self.active = active # used for device deactivation 
        self.logQ = deque()
        self.app = None

    def initialize_zigbee(self):
        # self.zigbee_network = zigpy.zigbee.api.zigbee_device(zigbee_channel=self.zigbee_channel)
        # self.zigbee_network.startup()

        self.app = zigpy.application.ControllerApplication()
        self.app.startup(auto_form=True, channel=self.zigbee_channel)

    def send(self, ieee: str, message: str):
        if self.app:
            device = self.app.get_device(ieee)
            if device:
                self.logQ.appendleft(message)
                print(f"Sending message: {message}")
                device.request(
                    profile=0x0104,
                    cluster=0x0006,
                    src_ep=1,
                    dst_ep=1,
                    sequence=0,
                    data=message.encode(),
                    expect_reply=False
                )


    def receive(self):
        if self.app:
            try:
                message = self.app._radio.receive()
                ieee = message.src.ieee
                print(f"Received message from {ieee}: {message.data.decode()}")
                return message.data.decode()
            except Exception as e:
                print(f"Error receiving message: {e}")
                return ""

    def activate(self):
        self.active.value = 1

    def deactivate(self):
        self.active.value = 0

    def check_status(self):
        return self.active.value
    

def main():
    active = multiprocessing.Value('i', 1) # activate the transciever
    zigbee_channel = 15 # zigbee supposedly has channels 11-26, each corresponding to a specific 2425 MHz frequency for sending messages

    transceiver = RobotTransceiver(zigbee_channel=zigbee_channel, active=active)
    transceiver.initialize_zigbee()

    # implement zigpy send function here
    transceiver.send_message("Test message")

    asyncio.run(transceiver.receive())

if __name__ == "__main__":
    main()
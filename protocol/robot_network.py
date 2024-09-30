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

        # self.app = zigpy.application.ControllerApplication()
        # self.app.startup(auto_form=True, channel=self.zigbee_channel)

        loop = asyncio.get_event_loop()
        self.app = loop.run_until_complete(zigpy.application.ControllerApplication.new())
        loop.run_until_complete(self.app.startup(auto_form=True, channel=self.zigbee_channel))
        print(f"Zigbee network started on channel {self.zigbee_channel}.")
        print(f"PAN ID: {self.app.pan_id}, Extended PAN ID: {self.app.extended_pan_id}")

    def send(self, message: str):
        # sends broadcast messages to all devices on network, not based on IEEE
        if self.app:
            # update nwk key after network is created on one of the transcievers
            broadcast_address = zigpy.types.Address(ieee=None, nwk=0xFFFF)
            print(f"Sending message: {message}")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                self.app.request(
                    broadcast_address,
                    profile=0x0104,
                    cluster=0x0006,
                    src_ep=1,
                    dst_ep=1,
                    sequence=0,
                    data=message.encode(),
                    expect_reply=False
                )
            )


    def receive(self):
        if self.app:
            try:
                listener = self.app.add_listener("device_message")
                loop = asyncio.get_event_loop()
                message = loop.run_until_complete(listener.wait_for_message())
                print(f"Received message: {message.data}")
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

    transceiver.send_message("Test message")

    asyncio.run(transceiver.receive())

if __name__ == "__main__":
    main()
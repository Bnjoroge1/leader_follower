import asyncio
import sys
import os
import time
import json
from protocol.ui_device import UIDevice
from protocol.device_classes import ThisDevice

class MockTransceiver:
    def __init__(self):
        self.incoming_channels = {}
        self.outgoing_channels = {}
    
    def set_incoming_channel(self, node_id, channel):
        self.incoming_channels[node_id] = channel
    
    def set_outgoing_channel(self, node_id, channel):
        self.outgoing_channels[node_id] = channel

class MockDeviceList:
    def get_device_list(self):
        return {
            "1": MockDevice(1, True, 0, 1),
            "2": MockDevice(2, False, 0, 2),
            "3": MockDevice(3, False, 0, 3),
            "4": MockDevice(4, False, 0, 4)
        }

class MockDevice:
    def __init__(self, id, is_leader, missed, task):
        self.id = id
        self.is_leader = is_leader
        self.missed = missed
        self.task = task
    
    def get_task(self):
        return self.task
    
    def get_leader(self):
        return self.is_leader
    
    def get_missed(self):
        return self.missed

async def main():
    print("Starting standalone UI WebSocket server")
    
    # Create a mock transceiver
    transceiver = MockTransceiver()
    
    # Create the UI device
    ui_device = UIDevice(5, transceiver)
    
    # Set up mock device list
    ui_device.device_list = MockDeviceList()
    
    # Start the WebSocket server
    print("Starting WebSocket server...")
    await ui_device.start_ws_server()

if __name__ == "__main__":
    asyncio.run(main())

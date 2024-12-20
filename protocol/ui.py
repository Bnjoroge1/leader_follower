import os
import time
from message_classes import Message, Action
from abstract_network import AbstractTransceiver
from zigbee_network import ZigbeeTransceiver
from typing import Any, Dict, List, Set
from pathlib import Path
import csv
from device_classes import ThisDevice, Device, TAKEOVER_DURATION
from enum import Enum
import websockets
import asyncio


class Status(Enum):
    DEAD = 0
    LEADER = 1
    FOLLOWER = 2


class UserInterface(ThisDevice):
    """ Contains backend logic for user interface """

    def __init__(self, transceiver: AbstractTransceiver, id=-1):
        super().__init__(transceiver=transceiver, id=id)
        self.devices: Dict[int, int] = {}

    def flag(self, tag, id):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If the loop is already running, use it to run the coroutine
                loop.run_until_complete(self.notify_server(f"{tag},{id}"))
            else:
                # If the loop is not running, use asyncio.run()
                asyncio.run(self.notify_server(f"{tag},{id}"))
        except RuntimeError:
            # If no event loop is available, create a new one
            asyncio.run(self.notify_server(f"{tag},{id}"))

    async def main(self):
        self.task = asyncio.create_task(self.websocket_client())  # asynchronous, no need to await return 
        
        while True:
            self.receive(duration=TAKEOVER_DURATION)
            action = self.received_action()

            if Action.ON.value:  # no fall through
                    follower_id = self.received_follower_id()
                    if follower_id not in self.device_list:
                        self.flag("NEW", follower_id)
                    self.devices[follower_id] = Status.FOLLOWER.value
                    self.flag("ALIVE", follower_id)
                    break
            elif Action.NEW_FOLLOWER.value:
                    follower_id = self.received_follower_id()
                    if follower_id not in self.device_list:
                        self.flag("NEW", follower_id)
                    self.devices[follower_id] = Status.FOLLOWER.value
                    self.flag("FOLLOWER", follower_id)
                    break
            elif Action.OFF.value:  # always sent in follower_id
                    follower_id = self.received_follower_id()
                    if follower_id not in self.devices:
                        self.flag("NEW", follower_id)
                    self.devices[follower_id] = Status.DEAD.value
                    self.flag("DEAD", follower_id)
                    break
            elif Action.NEW_LEADER.value:
                    leader_id = self.received_leader_id()
                    if leader_id not in self.devices:
                        self.flag("NEW", leader_id)
                    self.devices[leader_id] = Status.LEADER.value
                    self.flag("LEADER", follower_id)
                    break
            else:
                    pass
        
        await self.task

        
    # websocket client to connect to server.js and interact with injections
    async def websocket_client(self):
        uri = "ws://localhost:3000"  # server.js websocket server
        async with websockets.connect(uri) as websocket:
            await websocket.send(f"CONNECTED,BACKEND")  # initial connection message

            async for message in websocket:
                if isinstance(message, bytes):
                    message = message.decode("utf-8")
                print(f"Received message: {message}")
                msg = message.split(',')
                if len(msg) != 2:
                    continue
                tag, id = msg[0], msg[1]
                if tag == "TOGGLE":
                    device_id = int(id)
                    if self.devices[device_id] == Status.DEAD.value:
                        self.send(action=Action.ACTIVATE.value, payload=0, leader_id=0, follower_id=device_id)
                    else:
                        # always sent in follower id
                        self.send(action=Action.DEACTIVATE.value, payload=0, leader_id=0, follower_id=device_id)


    # called via asyncio from a synchronous environment - send, receive
    async def notify_server(self, message: str):
        uri = "ws://localhost:3000"  # server.js websocket server
        async with websockets.connect(uri) as websocket:
            await websocket.send(message)
    
            
if __name__ == "__main__":
    ui = UserInterface(transceiver=ZigbeeTransceiver())
    asyncio.run(ui.main())
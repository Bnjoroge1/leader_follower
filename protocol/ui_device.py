import time
import json
import asyncio
import threading
import websockets
from device_classes import ThisDevice, Device
from message_classes import Message, Action
from typing import Dict, List, Set

class UIDevice(ThisDevice):
    """
    Special device that only listens to the network and serves as a UI backend.
    It doesn't send messages to other devices, but forwards the data to the UI frontend.
    """
    def __init__(self, id, transceiver):
        super().__init__(id, transceiver)
        self.connected_clients = set()
        # Start WebSocket server in a separate thread
        self.ws_thread = threading.Thread(target=self.start_ws_server)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
    def start_ws_server(self):
        """Start WebSocket server in a separate thread"""
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        server = websockets.serve(self.ws_handler, "0.0.0.0", 8765)
        loop.run_until_complete(server)
        loop.run_forever()

    async def ws_handler(self, websocket, path):
        """Handle WebSocket connections from clients"""
        self.connected_clients.add(websocket)
        try:
            await websocket.send(json.dumps({
                "type": "initial_state",
                "device_id": self.id,
                "leader_id": self.leader_id,
                "is_leader": self.leader,
                "device_list": self.format_device_list()
            }))
            
            async for message in websocket:
                # We could handle commands from UI here
                pass
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_clients.remove(websocket)

    def format_device_list(self) -> List[Dict]:
        """Format device list for JSON serialization"""
        result = []
        for device_id, device in self.device_list.get_device_list().items():
            result.append({
                "id": device_id,
                "task": device.get_task(),
                "leader": device.get_leader(),
                "missed": device.get_missed()
            })
        return result

    async def broadcast_update(self, update_type, data):
        """Broadcast update to all connected clients"""
        if not self.connected_clients:
            return
            
        message = json.dumps({
            "type": update_type,
            "timestamp": time.time(),
            "data": data
        })
        
        await asyncio.gather(
            *[client.send(message) for client in self.connected_clients]
        )

    # Override methods to prevent sending messages
    def send(self, action: int, payload: int, leader_id: int, follower_id: int, duration: float = 0.0):
        """
        Override send to not actually send to the network
        """
        # Only log the message, don't actually send it
        msg = Message(action, payload, leader_id, follower_id).msg
        self.log_message(msg, 'WOULD_SEND')
        
        # Broadcast to UI clients instead
        asyncio.run(self.broadcast_update("message_log", {
            "type": "send",
            "action": action,
            "payload": payload,
            "leader_id": leader_id,
            "follower_id": follower_id
        }))

    def make_leader(self):
        """Override make_leader to not send any messages"""
        super(Device, self).make_leader()
        self.log_status("WOULD BECOME LEADER")
        asyncio.run(self.broadcast_update("status_change", {"is_leader": True}))

    def make_follower(self):
        """Override make_follower to not send any messages"""
        super(Device, self).make_follower()
        self.log_status("WOULD BECOME FOLLOWER")
        asyncio.run(self.broadcast_update("status_change", {"is_leader": False}))

    # Override receive to broadcast received messages to UI
    def receive(self, duration, action_value=-1) -> bool:
        """
        Gets first message heard from transceiver with specified action,
        and broadcasts it to connected UI clients.
        """
        # Use the original receive logic
        result = super().receive(duration, action_value)
        
        # If we received a message, broadcast it to UI
        if result and self.received:
            try:
                action = self.received_action()
                leader_id = self.received_leader_id()
                follower_id = self.received_follower_id()
                payload = self.received_payload()
                
                asyncio.run(self.broadcast_update("received_message", {
                    "action": action,
                    "leader_id": leader_id,
                    "follower_id": follower_id,
                    "payload": payload,
                    "raw": self.received
                }))
                
                # Also broadcast device list updates when appropriate
                if action in [Action.D_LIST.value, Action.DELETE.value]:
                    asyncio.run(self.broadcast_update("device_list", self.format_device_list()))
                
            except Exception as e:
                self.log_status(f"Error broadcasting message: {e}")
                
        return result

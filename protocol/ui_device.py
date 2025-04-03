from enum import Flag
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
        self.leader_id = None
        self._ws_server_running = False

    def device_main(self):
        # Initialize the WebSocket server 
        if not self._ws_server_running:
            print("Starting WebSocket server...")
            # Create a new event loop for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.ws_thread = threading.Thread(
                target=self.start_ws_server,
                daemon=True
            )
            self.ws_thread.start()
            self._ws_server_running = True
    async def start_ws_server(self):
        """Start WebSocket server in a separate thread"""
       
        if not self._ws_server_running:
            try:
                async with websockets.serve(self.ws_handler, "0.0.0.0", 8765):
                    print(f"WebSocket server started on port 8765")
                    self._ws_server_running = True
                    await asyncio.Future()  # Keep the server running
            except Exception as e:
                print(f"WebSocket server error: {e}")
                import traceback
                traceback.print_exc()

    def send_update(self, update_type, data):
        """Helper to send updates via the event loop without await issues"""
        if not self.loop:
            print("Warning: WebSocket event loop not initialized")
            return
            
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.broadcast_update(update_type, data), 
                self.loop
            )
            future.result(timeout=1.0)
        except Exception as e:
            print(f"Error scheduling update: {e}")

    async def ws_handler(self, websocket):
        """Handle WebSocket connections from clients"""
        client_address = websocket.remote_address
        print(f"WebSocket client connected from {client_address[0]}:{client_address[1]}")
        self.connected_clients.add(websocket)
        try:
            await websocket.send(json.dumps({
                "type": "initial_state",
                "device_id": self.id,
                "leader_id": self.leader_id if hasattr(self, 'leader_id') else None,
                "is_leader": self.leader if hasattr(self, 'leader') else False,
                "is_follower": not self.leader if hasattr(self, 'leader') else True,
                "is_ui": True,
                "device_list": self.format_device_list()
            }))
            
            async for message in websocket:
                print(f"Received message from client: {message}")
                # We could handle commands from UI here
                
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Client connection closed: {e}")
        finally:
            self.connected_clients.remove(websocket)
            print(f"Client disconnected: {client_address[0]}:{client_address[1]}")

    def format_device_list(self) -> List[Dict]:
        """Format device list for JSON serialization"""
        result = []
        print(f"ui gets device list: {self.device_list.get_device_list().items()}")
        for device_id, device in self.device_list.get_device_list().items():
            result.append({
                "id": device_id,
                "task": device.get_task(),
                "leader": device.get_leader(),
                "missed": device.get_missed()
            })
        return result
    def broadcast_update(self):
        """Send state update to all connected WebSocket clients"""
        if not self.connected_clients:
            return

        message = {
            "type": "state_update",
            "data": {
                "leader_id": self.leader_id if self.leader_id is not None else "none",
                "active_nodes": [node.id for node in self.device_list],
                "messages": []  # Add any message history you want to show
            }
        }
        print(f"DEBUG: Broadcasting state update: {message}")
        
        # Send to all connected clients
        for websocket in self.connected_clients:
            asyncio.create_task(websocket.send(json.dumps(message)))

    def update_leader(self, new_leader_id):
        """Update leader ID and notify all WebSocket clients"""
        self.leader_id = new_leader_id
        if self.loop:
            future = asyncio.run_coroutine_threadsafe(
                self.broadcast_update('leader_update', new_leader_id), 
                self.loop
            )
            try:
                future.result(timeout=1.0)
            except Exception as e:
                print(f"Error broadcasting leader update: {e}")


    def update_leader(self, new_leader_id):
        """Update leader ID and notify all WebSocket clients"""
        self.leader_id = new_leader_id
        self.broadcast_state_update()

    def broadcast_state_update(self):
        """Send state update to all connected WebSocket clients"""
        if not self.connected_clients:
            return
            
        message = {
            "type": "state_update",
            "data": {
                "leader_id": self.leader_id if self.leader_id is not None else "none",
                "active_nodes": [node.id for node in self.device_list],
                "messages": []  # Add any message history you want to show
            }
        }
        
        # Send to all connected clients
        for websocket in self.connected_clients:
            asyncio.create_task(websocket.send(json.dumps(message)))

    # Override methods to prevent sending messages
    def send(self, action: int, payload: int, leader_id: int, follower_id: int, duration: float = 0.0):
        """
        Override send to not actually send to the network
        """
        # Only log the message, don't actually send it
        msg = Message(action, payload, leader_id, follower_id).msg
        self.log_message(msg, 'WOULD_SEND')
        
        # Broadcast to UI clients instead
        self.send_update("message_log", {
            "type": "send",
            "action": action,
            "payload": payload,
            "leader_id": leader_id,
            "follower_id": follower_id
        })

    def make_leader(self):
        """Override make_leader to not send any messages"""
        super().make_leader()
        self.leader_id = self.id  # Update leader_id when becoming leader

        self.log_status("WOULD BECOME LEADER")
        if self._ws_server_running:
            self.send_update("status_change", {
                "is_leader": True,
                "leader_id": self.id
            })

    def make_follower(self):
        """Override make_follower to not send any messages"""
        super().make_follower()
        self.log_status("WOULD BECOME FOLLOWER")
        self.send_update("status_change", {"is_leader": False})

    # Override receive to broadcast received messages to UI
    def receive(self, duration, action_value=-1) -> bool:
        """
        Gets first message heard from transceiver with specified action,
        and broadcasts it to connected UI clients.
        """
        print(f"UI recv")
        # Use the original receive logic
        result = super().receive(duration, action_value)
        
        # If we received a message, broadcast it to UI
        if result and self.received:
            try:
                action = self.received_action()
                leader_id = self.received_leader_id()
                follower_id = self.received_follower_id()
                payload = self.received_payload()
                
                self.send_update("received_message", {
                    "action": action,
                    "leader_id": leader_id,
                    "follower_id": follower_id,
                    "payload": payload,
                    "raw": self.received
                })
                
                # Also broadcast device list updates when appropriate
                if action in [Action.D_LIST.value, Action.DELETE.value]:
                    self.send_update("device_list", self.format_device_list())
                
            except Exception as e:
                self.log_status(f"Error broadcasting message: {e}")
                
        return result
    
    # # purely for testing without robots
    # def device_main_mocked(self):
    #     """Override device_main to avoid requiring real messages"""        
    #     # Notify connected clients we're online
    #     self.send_update("status", {"status": "online"})
        
    #     # Set UI device to always be a follower
    #     self.leader = None
    #     self.device_role = "ui"
        
    #     # Create five mock devices for testing - initially device 1001 is the leader
    #     mock_devices = [
    #         {"id": 1001, "task": 1, "leader": True, "missed": 0, "role": "leader"},   # Position 1
    #         {"id": 1002, "task": 2, "leader": False, "missed": 0, "role": "follower"},  # Position 2
    #         {"id": 1003, "task": 3, "leader": False, "missed": 0, "role": "follower"},  # Position 3
    #         {"id": 1004, "task": 4, "leader": False, "missed": 0, "role": "follower"},  # Position 4
    #         {"id": 1005, "task": 5, "leader": False, "missed": 0, "role": "follower"},  # Position 5
    #     ]

    #     ui_device = {"id": self.id, "task": None, "leader": None, "missed": 0, "role": "ui"}
        
    #     # Set the initial leader ID
    #     current_leader_idx = 0
    #     self.leader_id = mock_devices[current_leader_idx]["id"]
        
    #     # For simulating device activities
    #     positions = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4}  # Maps position to device index
        
    #     # Just keep running - the WebSocket thread handles UI communication
    #     counter = 0
    #     try:
    #         while True:
    #             # Every 10 seconds, switch leader to another device (never UI device)
    #             if counter % 10 == 0 and counter > 0:
    #                 # Make current leader a follower
    #                 mock_devices[current_leader_idx]["leader"] = False
                    
    #                 # Pick a new leader (cycling through devices 0-4)
    #                 current_leader_idx = (current_leader_idx + 1) % 5
    #                 mock_devices[current_leader_idx]["leader"] = True
    #                 self.leader_id = mock_devices[current_leader_idx]["id"]
                    
    #                 # Broadcast leadership change
    #                 self.send_update("status_change", {
    #                     "is_leader": False,  # UI device is always follower
    #                     "leader_id": self.leader_id
    #                 })
    #                 print(f"New leader: Device {self.leader_id}")
                    
    #                 # Simulate leader sending attendance request
    #                 self.send_update("message_log", {
    #                     "type": "send",
    #                     "action": 1,  # ATTENDANCE
    #                     "payload": counter,
    #                     "leader_id": self.leader_id,
    #                     "follower_id": 0  # Broadcast to all
    #                 })
                
    #             # Every 15 seconds, move a random device to a new position
    #             if counter % 15 == 0 and counter > 0:
    #                 # Pick a random device to move
    #                 device_idx = counter % 5
    #                 old_task = mock_devices[device_idx]["task"]
                    
    #                 # Find an empty position or swap with another device
    #                 new_task = (old_task % 5) + 1
                    
    #                 # Update position mapping
    #                 if new_task in positions:
    #                     other_device_idx = positions[new_task]
    #                     mock_devices[other_device_idx]["task"] = old_task
    #                     positions[old_task] = other_device_idx
                    
    #                 # Set new task for moved device
    #                 mock_devices[device_idx]["task"] = new_task
    #                 positions[new_task] = device_idx
                    
    #                 # Broadcast task assignment
    #                 self.send_update("message_log", {
    #                     "type": "send",
    #                     "action": 3,  # ASSIGN_TASK
    #                     "payload": new_task,
    #                     "leader_id": self.leader_id,
    #                     "follower_id": mock_devices[device_idx]["id"]
    #                 })
    #                 print(f"Device {mock_devices[device_idx]['id']} moved to position {new_task}")
                
    #             # Every 8 seconds, simulate a heartbeat/ping
    #             if counter % 8 == 0:
    #                 # Leader pings a random follower
    #                 target_idx = (counter // 8) % 5
    #                 if target_idx != current_leader_idx:  # Don't ping self
    #                     self.send_update("message_log", {
    #                         "type": "send",
    #                         "action": 5,  # PING
    #                         "payload": 0,
    #                         "leader_id": self.leader_id,
    #                         "follower_id": mock_devices[target_idx]["id"]
    #                     })
                        
    #                     # Simulate follower response
    #                     self.send_update("received_message", {
    #                         "action": 6,  # PONG
    #                         "leader_id": self.leader_id,
    #                         "follower_id": mock_devices[target_idx]["id"],
    #                         "payload": 0,
    #                         "raw": 6000000000000
    #                     })
                
    #             # Every 17 seconds, simulate a device going inactive/active
    #             if counter % 17 == 0 and counter > 0:
    #                 inactive_idx = counter % 5
    #                 if inactive_idx != current_leader_idx:  # Don't make leader inactive
    #                     # Toggle missed count (0 = active, >0 = inactive)
    #                     mock_devices[inactive_idx]["missed"] = 0 if mock_devices[inactive_idx]["missed"] > 0 else 2
    #                     status = "inactive" if mock_devices[inactive_idx]["missed"] > 0 else "active"
    #                     print(f"Device {mock_devices[inactive_idx]['id']} is now {status}")
                
    #             # Every 5 seconds, broadcast updated device list
    #             if counter % 5 == 0:
    #                 self.send_update("device_list", mock_devices)
    #                 print("Device list updated")
                
    #             # Occasionally simulate arbitrary message exchange
    #             if counter % 23 == 0 and counter > 0:
    #                 # Random action type for variety
    #                 action_type = (counter % 7) + 1
    #                 self.send_update("received_message", {
    #                     "action": action_type,
    #                     "leader_id": self.leader_id,
    #                     "follower_id": mock_devices[counter % 5]["id"],
    #                     "payload": counter,
    #                     "raw": int(f"{action_type}00{self.leader_id}0{mock_devices[counter % 5]['id']}{counter}")
    #                 })
                
    #             counter += 1
    #             time.sleep(1)
    #     except KeyboardInterrupt:
    #         print("UI Device shutting down")
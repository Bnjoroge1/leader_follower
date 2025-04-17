import time
import json
import asyncio
import threading
from multiprocessing import Queue
import websockets 
from device_classes import Device, ThisDevice
from message_classes import Message, Action
from typing import Dict, List

class UIDevice(ThisDevice):
    """
    Special device that only listens to the network and serves as a UI backend.
    It doesn't send messages to other devices, but forwards the data to the UI frontend.
    """
    def __init__(self, id, transceiver, update_queue:Queue):
        super().__init__(id, transceiver)
        self.connected_clients = set()
        self.leader_id = 0  # Initialize with 0 instead of None
        self._ws_server_running = False
        
        self.is_ui_device = True
        self.is_leader = False
        self.device_list.add_device(id=self.id, task_index=0, thisDeviceId=self.id)
        self.csvWriter = None
        self.transceiver = transceiver
        self.update_queue = update_queue
        self.latest_device_list_cache: List[Dict] = [] 


    def log_status(self, status: str):
        pass # No logging for UI device
    def log_message(self, msg: int, direction: str):
        pass # No logging for UI device
    
        
    def device_main(self):
        """Main loop for the UI Device. Listens passively and updates UI."""
        print(f"--- UI Device Process {self.id} Entered device_main ---") # <-- ADD THIS LINE


        print("UI Device: Main loop started. Passively listening...")
        while True:
            try:
                # Listen directly using the transceiver with a short timeout
                received_msg_int = self.transceiver.receive(timeout=1.0)
                print(f"UI Device: Received message: {received_msg_int}")
                if received_msg_int is not None:
                    # Process the raw message
                    self._process_received_message(received_msg_int)
                else:
                    # Optional: Handle timeout (e.g., check connection status)
                    # print("UI Device: No message received in the last second.")
                    pass

                # Small sleep to prevent high CPU usage if receive returns immediately
                time.sleep(0.05)

            except Exception as e:
                print(f"Error in UI Device main loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1) # Avoid rapid error loops

    def _process_received_message(self, msg_int: int):
        """Processes a raw message received from the network."""
        list_changed = False
        leader_changed = False
        print(f"UI device processing received message: {msg_int}")
        try:
            # Parse the message using base class helpers (assuming self.received is set)
            self.received = msg_int # Temporarily set self.received for parsing methods
            action = self.received_action()
            leader_id = self.received_leader_id()
            follower_id = self.received_follower_id()
            payload = self.received_payload()
            self.received = None # Clear self.received after parsing

            print(f"UI Processed: Action={action}, Leader={leader_id}, Follower={follower_id}, Payload={payload}")

            # --- Update Leader ID ---
            current_leader = self.leader_id
            potential_new_leader = 0
            # Leader is identified by the leader_id field in most relevant messages
            if action == Action.CANDIDACY.value:
                # Heard a candidacy broadcast. The sender's ID is in leader_id_from_msg.
                candidate_id = leader_id
                print(f"UI device heard candidacy from device {candidate_id}")
                # If no leader is known OR this candidate has a lower ID than the current known leader,
                # update our internal leader_id. This tracks the *potential* winner.
                if candidate_id != 0 and (current_leader == 0 or candidate_id < current_leader):
                    potential_new_leader = candidate_id

            elif action == Action.ATTENDANCE.value:
                # Heard an attendance message from an established leader.
                established_leader_id = leader_id
                print(f"UI device received attendance from leader {established_leader_id}")
                if established_leader_id != 0:
                    # If this is different from our current leader OR we didn't have one, update.
                    # Attendance from the lowest ID leader confirms their leadership.
                    if current_leader == 0 or established_leader_id >= current_leader: # Use <= to accept the lowest ID leader
                         potential_new_leader = established_leader_id
                    # If we hear attendance from a HIGHER ID leader than we know, ignore it for leader update.
                    # The tiebreaker logic ensures the higher ID leader steps down 
            elif action == Action.NEW_LEADER.value:
                 # Explicit announcement of a new leader
                 announced_leader_id = leader_id
                 print(f"UI device received NEW_LEADER announcement for {announced_leader_id}")
                 if announced_leader_id != 0:
                      potential_new_leader = announced_leader_id
                 
            #apply the leader update
            if potential_new_leader != 0 and potential_new_leader != current_leader:
                self.leader_id = potential_new_leader
                leader_changed = True
                print(f"UI device updated leader to {self.leader_id}")   
                

            # --- Update Device List ---
            device_id_to_process = 0
            task_to_set = -1 # Use -1 to indicate no task update  

            # Determine which device ID this message gives us info about
            if action == Action.CANDIDACY.value:
                 device_id_to_process = leader_id # The candidate itself
            elif action == Action.ATTENDANCE.value or action == Action.NEW_LEADER.value:
                 device_id_to_process = leader_id # The leader sending attendance
            elif action in [Action.ATT_RESPONSE.value, Action.NEW_FOLLOWER.value, Action.CHECK_IN_RESPONSE.value]:
                device_id_to_process = follower_id # The follower responding/announcing
            elif action == Action.D_LIST.value: # Leader assigning task
                device_id_to_process = follower_id
                task_to_set = payload # Payload is the task
            elif action == Action.DELETE.value: # Leader removing device
                if follower_id != 0 and self.device_list.remove_device(id=follower_id):
                    print(f"UI Removed device {follower_id}")
                    list_changed = True
                device_id_to_process = 0 # Don't process further after removal


            # Add or update the device if identified
            if device_id_to_process != 0 and device_id_to_process != self.id: # Ignore self
                if device_id_to_process not in self.device_list.get_device_list().keys():
                    print(f"UI Check: Device {device_id_to_process} not in list {list(self.device_list.get_device_list().keys())}")

                existing_device_obj = self.device_list.find_device(device_id_to_process)
                print(f"UI Check: find_device({device_id_to_process}) returned: {existing_device_obj}")

                if not existing_device_obj:
                    # Add new device
                    # Determine initial task (use payload if D_LIST, else 0)
                    initial_task = task_to_set if task_to_set != -1 else 0
                    self.device_list.add_device(id=device_id_to_process, task_index=initial_task, thisDeviceId=self.id)
                    print(f"UI Added device {device_id_to_process} (Task: {initial_task}) based on Action {action}")
                    list_changed = True
                elif task_to_set != -1:
                    # Update existing device's task if D_LIST was received
                    device_obj = self.device_list.get_device_list().get(device_id_to_process)
                    if device_obj and device_obj.get_task() != task_to_set:
                        device_obj.set_task(task_to_set)
                        print(f"UI Updated task for {device_id_to_process} to {task_to_set}")
                        list_changed = True
                # Update 'missed' count (reset on hearing from device) - requires Device object modification
                # For now, just adding/updating task is sufficient based on messages

            # --- Broadcast Updates ---
            print(f"DEBUG: UI device preparng to queue message log")
            # Broadcast message log regardless
            self.send_update("message_log", {
                "type": "receive", # Indicate it was received by UI device
                "action": action, "leader_id": leader_id, "follower_id": follower_id,
                "payload": payload, "raw": msg_int, "device_id": self.id
            })

            # Broadcast leader update if changed
            if leader_changed:
                self.send_update("status_change", {
                    "is_leader": False, # UI is never leader
                    "leader_id": str(self.leader_id) # Send as string
                })
                # Leader change often implies device list might need refresh visually
                list_changed = True

            # Broadcast device list if it changed
            if list_changed:
                print(f"UI Device: List changed. Broadcasting update.")
                formatted_list = self.format_device_list()
                print(f"UI Device: Sending formatted list: {formatted_list}")
                self.send_update("device_list", formatted_list)

        except ValueError:
            print(f"UI Device: Error parsing received message {msg_int}")
        except Exception as e:
            print(f"UI Device: Error processing message {msg_int}: {e}")
            import traceback
            traceback.print_exc()

    async def start_ws_server(self):
        """Start WebSocket server in a separate thread"""

        if not self._ws_server_running:
            try:
                print("About to start WebSocket server on port 8765")
                async with websockets.serve(self.ws_handler, "0.0.0.0", 8765):
                    print(f"WebSocket server started on port 8765")
                    self._ws_server_running = True
                    await asyncio.Future()  # Keep the server running
            except Exception as e:
                print(f"WebSocket server error: {e}")
                import traceback
                traceback.print_exc()

    def send_update(self, update_type, data):
        """Puts the update onto the shared queue instead of using threadsafe calls."""
        try:
            # Put the update type and data onto the queue
            self.update_queue.put((update_type, data))
            # print(f"UI Device: Queued update - Type: {update_type}") # Can be noisy
        except Exception as e:
            # Handle potential queue errors (e.g., if queue is closed unexpectedly)
            print(f"Error putting update onto queue: {e}")

    async def ws_handler(self, websocket):
        """Handle WebSocket connections from clients"""
        client_address = websocket.remote_address
        print(f"WebSocket client connected from {client_address[0]}:{client_address[1]}")
        self.connected_clients.add(websocket)
        try:
            # Send initial state to the client
            device_list = self.latest_device_list_cache
            print(f"UI Device {self.id}: Using cached device list for initial state: {device_list}")
            initial_state = {
                "type": "initial_state",
                "device_id": str(self.id),  # Ensure it's a string
                "leader_id": str(self.leader_id) if self.leader_id else "0",  # Ensure it's a string
                "is_leader": False,  # UI device is always follower
                "device_list": device_list
            }

            print(f"Sending initial state: {initial_state}")
            await websocket.send(json.dumps(initial_state))

            # Also send a separate device list update
            #await self.broadcast_update("device_list", device_list)

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
        try:
            print(f"ui gets device list: {self.device_list.get_device_list()}")
            current_leader = self.leader_id
            print(f"ui gets device list: {self.device_list.get_device_list().items()}")
            for device_id, device in self.device_list.get_device_list().items():
                if isinstance(device, Device):
                    print(f"ui gets device: {device}")
                    result.append({
                    "id": device_id,
                    "task": device.get_task(),
                    "leader": device_id == current_leader,
                    "missed": device.get_missed()
                    })
                else:
                    print(f"ui is not an instance of ThisDevice")
            print(f"Formatted device list: {result}")
        except Exception as e:
            print(f"Error formatting device list: {e}")
            # If we can't get the real device list, create a mock one for testing
            result = []
        return result
    async def broadcast_update(self, device_list_update, data):
        """Send update to all connected WebSocket clients"""
        if not self.connected_clients:
            return

        message = { # type: ignore      
            "type": device_list_update,
            "timestamp": time.time(),
            "data": data
        } 
        print(f"DEBUG: Broadcasting update: {message}")

        # Send to all connected clients
        for websocket in self.connected_clients:
            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                print(f"Error sending to client: {e}")
                # Remove disconnected clients
                if websocket in self.connected_clients:
                    self.connected_clients.remove(websocket)

    def update_leader(self, new_leader_id):
        """Update leader ID and notify all WebSocket clients"""
        self.leader_id = new_leader_id
        self.send_update('leader_update', {
            "leader_id": new_leader_id
        })


    def broadcast_device_list_update(self):
        """Send state update to all connected WebSocket clients"""
        if not hasattr(self, 'device_list') or not self.device_list:
            return

        self.send_update("device_list", {
            "leader_id": self.leader_id if self.leader_id is not None else "none",
            "device_list": self.format_device_list()
        })

    # --- Ensure Overrides Prevent Network Participation ---
def send(self, action: int, payload: int, leader_id: int, follower_id: int, duration: float = 0.0):
    """Override send to prevent network transmission and log to UI."""
    msg = Message(action, payload, leader_id, follower_id).msg
    # Log that we *would* send, but don't call self.transceiver.send()
    print(f"UI Device {self.id}: Would send Action={action}, L={leader_id}, F={follower_id}, P={payload}")
    # Broadcast to UI clients instead
    self.send_update("message_log", {
        "type": "would_send", # Indicate it wasn't actually sent on network
        "action": action, "payload": payload, "leader_id": leader_id,
        "follower_id": follower_id, "device_id": self.id, "raw": msg
    })

def _perform_leader_election(self):
    print(f"UI Device {self.id}: Skipping leader election.")
    return 0 # Never elects self

def broadcast_candidacy(self):
    print(f"UI Device {self.id}: Skipping candidacy broadcast.")
    pass # Do nothing

def make_leader(self):
     print(f"UI Device {self.id}: Cannot become leader.")
     self.leader = False # Ensure always follower
     self.leader_id = 0 # Reset leader ID if somehow called

def make_follower(self, determined_leader_id: int = 0):
     print(f"UI Device {self.id}: Ensuring follower state (Heard leader: {determined_leader_id}).")
     self.leader = False
     # Update internal leader_id if a valid one is provided
     if determined_leader_id != 0 and self.leader_id != determined_leader_id:
          self.leader_id = determined_leader_id
          self.send_update("status_change", {"is_leader": False, "leader_id": str(self.leader_id)})
     # Don't send NEW_FOLLOWER message to network

    

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
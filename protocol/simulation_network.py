from dataclasses import asdict, dataclass
import json
from re import L
import time
import device_classes as dc
import multiprocessing
from multiprocessing import Queue
import queue as q
from queue import Empty
from typing import Any, Dict, Optional, Set
from abstract_network import AbstractNode, AbstractTransceiver
import asyncio
import websockets
import threading
from message_classes import Message
from collections import deque
import hashlib
from checkpoint_manager import CheckpointManager
from device_state import DeviceState


class SimulationNode(AbstractNode):

    def __init__(self, node_id: int,  active_value: int, target_func = None, target_args = None,  checkpoint_mgr: Optional[CheckpointManager] = None):  # type: ignore
        self.node_id = node_id
        self._active_value = active_value
        self.transceiver = SimulationTransceiver(active_value=active_value, parent_id=node_id)
        self.transceiver.parent_id = node_id
        self.checkpoint_mgr = checkpoint_mgr
        self.trace_enabled = False
        self.SECRET_KEY = "secret_key"
        self.thisDevice = dc.ThisDevice(self.__hash__() % 10000, self.transceiver)
        self.target_func = target_func if target_func is not None else self.thisDevice.device_main 
        
        self._main_task: Optional[asyncio.Task] = None 

    def join(self) ->None:
        '''satisfy abstract class'''
        raise NotImplementedError
        
            
    
    
    def deactivate(self):
        self._active_value = 0
        

    def reactivate(self):
        self._active_value = 1
        

    def stay_active(self):
        self._active_value = 2

    def active_status(self):
        return self._active_value
    def generate_device_id(self, node_id):
        # Combine node_id and secret key
        input_string = f"{self.SECRET_KEY}{node_id}"
        
        # Generate SHA-256 hash
        hash_object = hashlib.sha256(input_string.encode())
        hash_hex = hash_object.hexdigest()
        
        # Truncate to 64 bits (16 hexadecimal characters)
        device_id = int(hash_hex[:16], 16)
        
        return device_id
    
    

    async def start(self):
        """Starts the node's main execution task asynchronously."""
        # Check if task already exists and is running
        if self._main_task and not self._main_task.done():
            print(f"Node {self.node_id} main task is already running.")
            return # Don't start again

        if self.target_func:
            print(f"Node {self.node_id}: Creating main task for {getattr(self.target_func, '__name__', 'target_func')}")
            # Create the task that runs the node's main logic (e.g., thisDevice.device_main)
            # Ensure self.target_func is awaitable (it should be if it's device_main)
            self._main_task = asyncio.create_task(self.target_func())
            # Optional: Add a callback for when the task finishes or errors
            # self._main_task.add_done_callback(self._handle_task_completion)
            print(f"Node {self.node_id}: Main task created: {self._main_task}")
        else:
            print(f"WARN: Node {self.node_id} has no target_func to start.")
    def log_message(self, msg: int, direction: str):
        self.thisDevice.log_message(msg, direction)

    def log_status(self, status: str):
        self.thisDevice.log_status(status)
        
    async def _async_stop(self):
        """Internal async implementation to stop the node's task"""
        if self._main_task and not self._main_task.done():
                # usually stop should be called from an async context
            print(f"DEBUG: Stopping task for node {self.node_id}")
            self._main_task.cancel()
            try:
                await self._main_task # Wait for cancellation to complete
            except asyncio.CancelledError:
                print(f"Task for node {self.node_id} cancelled successfully.")
            except Exception as e:
                 print(f"Error during task cancellation for node {self.node_id}: {e}")
            self.log_status(f"Node {self.node_id} stopped")
        self._main_task = None

    def stop(self) -> None: # Synchronous interface method
        """Stop the node's task (synchronous wrapper)."""
        print(f"DEBUG: Initiating stop for node {self.node_id}")
        try:
            # Get existing loop or create new one
            try:
                import channel_driver
                #get the main event loop
                event_loop = channel_driver.main_event_loop
                if not event_loop:
                    print(f"ERROR: Main event loop not accessible for stop to work.")
                    return
                    
            except RuntimeError:
                # Only create a new loop if absolutely necessary,
                # or the main thread managing the loop.
                #we shouldnt be getting here. 
                print(f"WARNING: Cant get event loop for main to stop the node")
                
                return

            # Run async stop operation
            if self._main_task and not self._main_task.done():
                event_loop.call_soon_threadsafe(self._main_task.cancel)
                print(f"DEBUG: cancelleaton requested for node {self.node_id}")
                self._main_task = None
                self.thisDevice.active = False  #helps
            else:
                 print(f"Main device is not running{self.node_id}")

        except Exception as e:
            print(f"Error in sync stop wrapper for node {self.node_id}: {e}")

    def set_incoming_channel(self, target_node_id, queue):
        self.transceiver.set_incoming_channel(target_node_id, queue)

    async def async_init(self):  # SimulationTransceiver
        await self.transceiver.websocket_client()
    
    
    
    


    

class Network:

    def __init__(self, manager=None):
        self.nodes: Dict[int, SimulationNode] = {}
        self.incoming_queue: Dict[int, asyncio.Queue] = {}
        self.topology: Dict[int, Set[int]] = {}  #adjacency list of node_id: set of adjacent nodes. 
       

    def add_node(self, node_id, node):
        if node_id not in self.nodes:
            self.nodes[node_id] = node
            #create the incoming queue
            self.incoming_queue[node_id] = asyncio.Queue()
            self.topology[node_id] = set()
            
           # Assign the queue and network reference to the node's transceiver
            if hasattr(node, 'transceiver') and isinstance(node.transceiver, SimulationTransceiver):
                # Assign the specific queue for this node_id
                node.transceiver._incoming_queue = self.incoming_queue.get(node_id)
                node.transceiver.network = self
                # --- ADD THIS ---
                # If the node has a ThisDevice instance, assign the transceiver to it too
                if hasattr(node, 'thisDevice') and node.thisDevice:
                    if hasattr(node.thisDevice, 'transceiver'):
                         print(f"Network: Assigning transceiver to node {node_id}'s ThisDevice instance.")
                         node.thisDevice.transceiver = node.transceiver
                    else:
                         print(f"WARN: Node {node_id}'s ThisDevice instance has no 'transceiver' attribute.")
                        
                        
            
            print(f"Network: Added node {node_id} and {node.transceiver.incoming_channels} channels.")
        else:
            print(f"Warn: Node {node_id} already exists. ")
    def get_node(self, node_id):
        return self.nodes.get(node_id)

    def create_channel(self, node_id1, node_id2):
        if node_id1 in self.topology and node_id2 in self.topology:
            self.topology.setdefault(node_id1, set()).add(node_id2)
            self.topology.setdefault(node_id2, set()).add(node_id1)
            # Crucially, update transceivers with references to the *other* node's incoming queue
            node1 = self.nodes[node_id1]
            node2 = self.nodes[node_id2]
            queue_for_node1 = self.incoming_queue.get(node_id1)
            queue_for_node2 = self.incoming_queue.get(node_id2)
            if hasattr(node1, 'transceiver') and queue_for_node2:
                node1.transceiver._outgoing_channels[node_id2] = queue_for_node2
            if hasattr(node2, 'transceiver') and queue_for_node1:
                 node2.transceiver._outgoing_channels[node_id1] = queue_for_node1
            print(f"Network: Created link between {node_id1} and {node_id2}")
        else:
             print(f"WARN: Cannot create channel, one or both nodes not found: {node_id1}, {node_id2}")


    async def distribute_message(self, sender_id, msg):
        """Distributes a message from sender_id to all connected nodes."""
        if sender_id not in self.topology:
            print(f"WARN: Sender {sender_id} not in network topology.")
            return

        #print(f"Network: Distributing message from {sender_id} to {self.topology[sender_id]}")
        for receiver_id in self.topology[sender_id]:
            if receiver_id in self.incoming_queue:
                try:
                    # Put the message into the receiver's incoming queue
                    # print(f"Network: Putting message for {receiver_id}") # Can be noisy
                    await self.incoming_queue[receiver_id].put(msg)
                except Exception as e:
                    print(f"Error putting message into queue for {receiver_id}: {e}")
            else:
                print(f"WARN: Receiver {receiver_id} (connected to {sender_id}) has no channel queue.")



class NetworkVisualizer:

    def __init__(self):
        pass

    def ui_main(self):
        pass



         



# TODO: implement removing channels (node_ids) as devices get dropped from devicelist
# similar implementation to send/receive calling transceiver functions
class SimulationTransceiver(AbstractTransceiver):

    

    def __init__(self, active_value=0, parent_id: int = None, network=None):  # type: ignore
        
        self._incoming_queue: Optional[asyncio.Queue] = None
        self._outgoing_channels : Dict[int, asyncio.Queue] = {}
        #self.parent = parent
        self.parent_id = parent_id
        #self._active_value = active.value if active else 2
        self._active_value = active_value  # just a simple value not a synchronized object. 
        self.network = network
        self.logQ = asyncio.Queue()

        print(f"DEBUG: Creating transceiver for device {parent_id}")
        print(f"DEBUG: Ougoing channels: {self._outgoing_channels}")
        print(f"DEBUG: Incoming channels: {self._incoming_queue}")

    @property
    def outgoing_channels(self):
        return self._outgoing_channels
        

    @property
    def incoming_channels(self):
        return self._incoming_queue

   

    async def _async_log(self, data:str):
        await self.logQ.put(data)

    async def log(self, data: str):
        """ Method for protocol to load aux data into transceiver """
        value = await self._async_log(data)

    def deactivate(self):
        self._active_value = 0
        

    def reactivate(self):
        self._active_value = 1
        

    def stay_active(self):
        self._active_value = 2

    def active_status(self):
        return self._active_value

    def set_outgoing_channel(self, node_id, queue: asyncio.Queue):
        #self.outgoing_channels[node_id] = queue
        #print(f"DEBUG: Outgoing channel set for node {self.parent_id} to {node_id}")
        pass

    def set_incoming_channel(self, node_id, queue: asyncio.Queue):
        #self.incoming_channels[node_id] = queue
        print(f"DEBUG: Incoming channel set for node {self.parent_id} to {node_id}")

    # Synchronous wrapper method matching the base class signature
    def send(self, msg: int) -> None:
        """
        Sends a message to all outgoing channels.

        This method is synchronous to comply with the AbstractTransceiver interface
        but uses asyncio internally to handle asynchronous sending.
        """
        print(f"DEBUG: Device {self.parent_id} attempting synchronous send")
        try:
            # Get the current event loop if one exists
            loop = asyncio.get_event_loop()
            # Run the async logic in current loop
            loop.run_until_complete(self.async_send(msg))
        except RuntimeError:
            # If no loop exists, create one temporarily
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.async_send(msg))
            finally:
                loop.close()

    async def async_send(self, msg: int) -> None:
        """Asynchronous send operation."""
        send_tasks = []
        if self.network:
            # Option 2: Send directly using stored outgoing refs
            for target_node_id, queue_ref in self._outgoing_channels.items():
                send_tasks.append(queue_ref.put(msg))
            if send_tasks:
                await asyncio.gather(*send_tasks)
            else:
                print(f"WARN: Node {self.parent_id} has no outgoing channel refs to send to.")
        else:
            print(f"WARN: Transceiver {self.parent_id} has no network reference.")

       

   

    async def async_receive(self, timeout: float) -> Optional[int]:
        """Asynchronous part of the receive logic using asyncio.wait."""
        print(f"DEBUG: Async receive logic started for {self.parent_id} with timeout={timeout}")
        if not self._incoming_queue:
            print(f'DEBUG: No incoming queue to receive from for {self.parent_id}.')
            if timeout > 0:
                await asyncio.sleep(timeout)
            return None


        try:
            msg = await asyncio.wait_for(self._incoming_queue.get(), timeout=timeout if timeout > 0 else None)
            # Mark task as done for the queue
            self._incoming_queue.task_done()

            # print(f"DEBUG: Device {self.parent_id} Received message {str(msg)}") # Can be noisy
            try:
                # Notify server (if running)
                await self.notify_server(f"RCVD,{self.parent_id}")
            except OSError:
                 # print(f"DEBUG: OSError notifying server for {self.parent_id}") # Can be noisy
                 pass
            except Exception as e:
                 print(f"DEBUG: Error notifying server for {self.parent_id}: {e}")
            return msg

        except asyncio.TimeoutError:
            # print(f'DEBUG: No messages received within timeout for {self.parent_id}') # Can be noisy
            return None
        except asyncio.CancelledError:
            print(f"DEBUG: Receive task was cancelled for {self.parent_id}")
            return None
        except Exception as e:
            print(f"DEBUG: Unexpected error in async receive logic for {self.parent_id}: {e}")
            return None


    # Synchronous wrapper method matching the base class signature Optional[int]
    def receive(self, timeout: float) -> Optional[int]:
        """
        Receives a message from any incoming channel.

        This method is synchronous to comply with the AbstractTransceiver interface
        but uses asyncio internally to handle multiple asynchronous queues.
        """
        print(f"DEBUG: Device {self.parent_id} attempting synchronous receive with timeout={timeout}")

        # Check device active status first
        active_status = self.active_status()
        if active_status == 0:
            print(f"DEBUG: Device {self.parent_id} is inactive, returning DEACTIVATE")
            return Message.DEACTIVATE
        if active_status == 1:
            print(f"DEBUG: Device {self.parent_id} was activating, now staying active, returning ACTIVATE")
            self.stay_active()
            return Message.ACTIVATE

        # Run the asynchronous receiving logic using asyncio.run()
        # This creates a new event loop for this specific call.
        result = None
        try:
            # Get the current event loop if one exists
            loop = asyncio.get_event_loop()
            # Run the async logic in current loop
            return loop.run_until_complete(self.async_receive(timeout))
        except RuntimeError:
            # If no loop exists, create one temporarily
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.async_receive(timeout))
            finally:
                loop.close()


    def clear(self):
        # Need to clear asyncio.Queue carefully
        for queue in self.incoming_channels.values(): # type: ignore
            while not queue.empty():
                try:
                    queue.get_nowait()
                    queue.task_done() # Mark task as done if using JoinableQueue, though asyncio.Queue doesn't strictly need it here
                except asyncio.QueueEmpty:
                    break # Queue is empty
                except Exception as e:
                    print(f"Error clearing queue item for {self.parent_id}: {e}")

   

    async def handle_tiebreaker(self, other_id):
        """Log tiebreaker events for visualization"""
        message = {
            'device_id': self.parent_id,
            'other_id': other_id,
            'type': 'TIEBREAKER',
            'timestamp': time.time()
        }
        
    # websocket client to connect to server.js and interact with injections
    async def websocket_client(self):
        uri = "ws://localhost:8765"  # server.js websocket server
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    await websocket.send(f"CONNECTED,{self.parent_id}")  # initial connection message

                    async for message in websocket:
                        if isinstance(message, bytes):
                            message = message.decode("utf-8")

                        print(f"Received message: {message}")
                        # Leadership changes cause red/blue transitions    
                        if "LEADER" in message:
                            await self.notify_state_change("FOLLOWER", "LEADER")
                        elif "FOLLOWER" in message:
                            await self.notify_state_change("LEADER", "FOLLOWER")
                        elif "TIEBREAKER" in message:
                            await self.handle_tiebreaker(message.split(",")[1])
                        if message == "Toggle Device":
                            print("Toggling device")
                            if self.active_status() == 0:  # been off
                                self.reactivate()  # goes through process to full activation
                                await websocket.send(f"REACTIVATED,{self.parent.node_id}")  # reactivation
                            else:
                                self.deactivate()  # recently just turned on
                                await websocket.send(f"DEACTIVATED,{self.parent.node_id}")  # deactivation
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed, reconnecting...")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"WebSocket error: {e}, reconnecting...")
                await asyncio.sleep(1)
    # called via asyncio from a synchronous environment - send, receive
    async def notify_server(self, message: str):
        uri = "ws://localhost:3000"  # server.js websocket server
        async with websockets.connect(uri) as websocket:
            await websocket.send(message)
    
            
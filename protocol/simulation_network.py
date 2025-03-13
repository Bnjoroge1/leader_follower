from dataclasses import asdict, dataclass
import time
import device_classes as dc
import multiprocessing
from multiprocessing import Queue
import queue as q
from queue import Empty
from typing import Any, Dict, Optional
from abstract_network import AbstractNode, AbstractTransceiver
import asyncio
import websockets
import threading
from message_classes import Message
from collections import deque
import hashlib
from checkpoint_manager import CheckpointManager

def device_process_function(device_id: int, node_id: int, active_value: int, outgoing_channels: Dict[int, Queue], incoming_channels: Dict[int, Queue]):
    """Standalone function for the device process"""
    try:
        # Create fresh active value
        active = multiprocessing.Value('i', active_value)
        # Create a dummy parent node to hold the node_id
        class DummyParent:
            def __init__(self, node_id):
                self.node_id = node_id
        # Create fresh transceiver with the channel dictionaries from the parent
        transceiver = SimulationTransceiver(active=active, parent_id=node_id)
        transceiver._outgoing_channels = outgoing_channels
        transceiver._incoming_channels = incoming_channels
        
        # Create fresh device
        device = dc.ThisDevice(device_id, transceiver)
        
        # Run device main
        device.device_main()
    except Exception as e:
        print(f"Error in device process: {e}")
        import traceback
        traceback.print_exc()
        raise
class SimulationNode(AbstractNode):

    def __init__(self, node_id, target_func = None, target_args = None, active: multiprocessing.Value = None, checkpoint_mgr: Optional[CheckpointManager] = None):  # type: ignore
        self.node_id = node_id
        self.active = active
        self.transceiver = SimulationTransceiver(active=active, parent_id=node_id)
        self.transceiver.parent_id = node_id
        self.checkpoint_mgr = checkpoint_mgr
        self.trace_enabled = False
        self.SECRET_KEY = "secret_key"
        self.process = None
        self.thisDevice = dc.ThisDevice(self.__hash__() % 10000, self.transceiver)
        # self.thisDevice = dc.ThisDevice(self.generate_device_id(node_id), self.transceiver)
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
            
    
    
    def generate_device_id(self, node_id):
        # Combine node_id and secret key
        input_string = f"{self.SECRET_KEY}{node_id}"
        
        # Generate SHA-256 hash
        hash_object = hashlib.sha256(input_string.encode())
        hash_hex = hash_object.hexdigest()
        
        # Truncate to 64 bits (16 hexadecimal characters)
        device_id = int(hash_hex[:16], 16)
        
        return device_id
    async def async_init(self):  # SimulationTransceiver
        await self.transceiver.websocket_client()
    

    def start(self):
        """Start the node's process"""
        if self.process is None or not self.process.is_alive():
            try:
                print(f"DEBUG: Starting process for node {self.node_id}")
                print(f"DEBUG: Device state before process start: {self.thisDevice.__dict__}")
                print(f"DEBUG: Transceiver state: {self.transceiver.__dict__}")
                if not hasattr(self, 'process') or self.process is None:
                    new_active = multiprocessing.Value('i', self.active.value)
                    #self.transceiver.active = new_active
                    device_state = {
                        'id': self.thisDevice.id,
                        'leader': self.thisDevice.leader,
                        'received': self.thisDevice.received,
                        'missed': self.thisDevice.missed,
                        'task': self.thisDevice.task,
                        'active': True
                    }

                    self.process = multiprocessing.Process(
                        target=device_process_function,
                        args=(
                            self.thisDevice.id,  # device_id
                            self.node_id,        # node_id
                            self.active.value,   # active_value
                            self.transceiver._outgoing_channels,
                            self.transceiver._incoming_channels,
                        ),
                        daemon=True
                    )
                self.process.start()
                print(f"Started process for node {self.node_id}")
            except Exception as e:
                print(f"Error starting process for node {self.node_id}: {e}")
                raise
    
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

    async def async_init(self):  # SimulationTransceiver
        await self.transceiver.websocket_client()
    
    def get_queue_state(self) -> Dict[str, Any]:
        """Captures queue state for checkpointing"""
        print(f"\nDEBUG: Starting queue state capture for node {self.node_id}")

        queue_state = {
            'incoming': {},
            'outgoing': {}
        }
        print(f"DEBUG: Capturing incoming channels: {self.transceiver.incoming_channels.values()}")

        
        # Save incoming queues
        for node_id, channel in self.transceiver.incoming_channels.items():
            messages = []
            try:
                
                print(f"DEBUG: Capturing incoming queue for channel {node_id}")
                print(f"DEBUG: Channel queue empty? {channel.queue.empty()}")
                # Create temporary queue to preserve original
                temp_queue = Queue()
                while not channel.queue.empty():
                    msg = channel.queue.get()
                    print(f"DEBUG: Got message from incoming queue: {msg}")
                    messages.append(msg)
                    temp_queue.put(msg)
                    print(f"DEBUG: Put message in temp queue: {msg}")
                    
                # Restore original queue
                print(f"DEBUG: Restoring original queue")
                while not temp_queue.empty():
                    channel.queue.put(temp_queue.get())
                    print(f"DEBUG: Put message in original queue: {msg}")
                    
                queue_state['incoming'][str(node_id)] = messages.copy()
                print(f"DEBUG: Incoming queue state for node {node_id}: {queue_state['incoming'][str(node_id)]}")
                
            except Exception as e:
                print(f"Error capturing incoming queue state for node {node_id}: {e}")
        print(f"DEBUG: Capturing outgoing channels: {self.transceiver.outgoing_channels.keys()}")

        # Save outgoing queues
        for node_id, channel in self.transceiver.outgoing_channels.items():
            messages = []
            temp_queue = Queue()
            try:
                print(f"DEBUG: Capturing outgoing queue for channel {node_id}")
                print(f"DEBUG: Channel queue empty? {channel.queue.empty()}")
                
                
                while not channel.queue.empty():
                    msg = channel.queue.get()
                    print(f"DEBUG: Got message from outgoing queue: {msg}")
                    messages.append(msg)
                    temp_queue.put(msg)
                    print(f"DEBUG: Put outgoing message in temp queue: {msg}")

                # Restore original queue
                print(f"DEBUG: Restoring original outgoing queue")
                while not temp_queue.empty():
                    msg = temp_queue.get()
                    channel.queue.put(msg)
                    print(f"DEBUG: Put outgoing message in original queue: {msg}")
                queue_state['outgoing'][str(node_id)] = messages.copy()
            except Exception as e:
                print(f"Error capturing outgoing queue state for node {node_id}: {e}")
        print(f"DEBUG: Final queue state for node {self.node_id}: {queue_state}")

        return queue_state

    def restore_from_checkpoint(self, node_state: Dict[str, Any], queue_state: Dict[str, Any] = None):
        """Restores node state from checkpoint data"""
        print(f"Restoring node {self.node_id} from state: {node_state}")  
        print(f"Queue state: {queue_state}")  
        
        self.node_id = node_state['node_id']
        active_value =  node_state.get('active', 2)
        self.active = None
        if hasattr(self, 'active'):
            old_active = self.active
            self.active = multiprocessing.Value('i', active_value)
            print("restored active value from old value to new value in checkpoint", active_value)
        else:
            self.active = multiprocessing.Value('i', active_value)
        self.transceiver.active = self.active
        print("restored active value from cehckpoint", active_value)
        
        # Restore device state
        if 'device_state' in node_state:
            self.thisDevice.restore_state(node_state['device_state'])
            
        
        print("Resoritng queue state: ", queue_state)
        # Restore queue state if provided
        if queue_state:
            self.restore_queue_state(queue_state) 

    def restore_queue_state(self, queue_state: Dict[str, Any]): 
        """Restores queue state from checkpoint data"""
        print(f"Restoring queues for node {self.node_id}")
        print(f"Queue state structure: {queue_state.keys()}")
        
        try:
            #create channels
            for node_id in queue_state.get('incoming', {}).keys():
                print(f"creating incoming channel for {node_id}")
                if str(node_id) not in self.transceiver.incoming_channels:
                    self.transceiver.incoming_channels[str(node_id)] = ChannelQueue()
                
            for node_id in queue_state.get('outgoing', {}).keys():
                print(f"creating outgoing channel for {node_id}")
                if str(node_id) not in self.transceiver.outgoing_channels:
                    self.transceiver.outgoing_channels[str(node_id)] = ChannelQueue()

            # Restore messages to existing queues
            for node_id, messages in queue_state.get('incoming', {}).items():
                print(f"Restoring incoming queues from node id {node_id}: {messages}")
                if str(node_id) in self.transceiver.incoming_channels:
                    channel = self.transceiver.incoming_channels[str(node_id)]
                    # Clear existing messages
                    while not channel.queue.empty():
                        try:
                            channel.queue.get_nowait()
                        except:
                            pass
                    # Add new messages
                    for msg in messages:
                        channel.queue.put(msg)
                        
            for node_id, messages in queue_state.get('outgoing', {}).items():
                print(f"Restoring outgoing messages to node {node_id}: {messages}")
                if str(node_id) in self.transceiver.outgoing_channels:
                    channel = self.transceiver.outgoing_channels[str(node_id)]
                    # Clear existing messages
                    while not channel.queue.empty():
                        try:
                            channel.queue.get_nowait()
                        except:
                            pass
                    # Add new messages
                    for msg in messages:
                        channel.queue.put(msg)

            print(f"DEBUG: Channels after restore: "
                f"incoming={self.transceiver.incoming_channels.keys()}, "
                f"outgoing={self.transceiver.outgoing_channels.keys()}")
                
        except Exception as e:
            import traceback
            print(f"Error restoring queue state:")
            print(traceback.format_exc())

    def trace_point(self, point_name: str):
        """Called at trace points to potentially checkpoint"""
        if self.checkpoint_mgr and self.checkpoint_mgr.should_checkpoint(point_name):
            print(f"Creating checkpoint at {point_name} for node {self.node_id}")
            self.checkpoint_mgr.create_checkpoint(f"trace_{point_name}", {self.node_id: self})
            print(f"Checkpoint created for {point_name}")

    def _get_process_state(self) -> Dict[str, Any]:
        """Captures process state"""
        return {
            'pid': self.process.pid if self.process else None,
            # Add other relevant process state
        }

    def _restore_queues(self, queue_state: Dict[str, Any]):
        """Restores queue state"""
        for node_id, messages in queue_state['incoming'].items():
            for msg in messages:
                self.transceiver.incoming_channels[node_id].put(msg)
        for node_id, messages in queue_state['outgoing'].items():
            for msg in messages:
                self.transceiver.outgoing_channels[node_id].put(msg)
    def set_process(self, process_func):
        """Sets the process function to be run by this node"""
        if self.process is not None and self.process.is_alive():
            self.process.terminate()
            
        # Create new active value for the process
        if self.active is None:
            self.active = multiprocessing.Value('i', 2)  # 2 is the default "active" state
            
        self.process = multiprocessing.Process(
            target=device_process_function,
            args=(
                self.thisDevice.id,  # device_id
                self.node_id,        # node_id 
                self.active.value,   # active_value
            ),
            daemon=True
        )
        print(f"Process set for node {self.node_id} with function {process_func.__name__}")
        
        # Update the device's process
        self.thisDevice.device_main = process_func
    def get_checkpoint_state(self) -> Dict[str, Any]:
        """Captures node state for checkpointing"""
        state = NodeState(
            node_id=self.node_id,
            active=self.active.value,
            device_state=self.thisDevice.get_state(),
            process_state=self._get_process_state()
        )
        return asdict(state)
    def _restore_process_state(self, state: Dict[str, Any]):
        """Restores process state from checkpoint"""
        if state.get('is_running', False):
            # If process was running in checkpoint, start a new process
            if not hasattr(self, 'process') or not self.process.is_alive():
                self.process = multiprocessing.Process(target=self.thisDevice.device_main)
                self.process.start()
        else:
            # If process wasn't running, make sure it's stopped
            if hasattr(self, 'process') and self.process.is_alive():
                self.process.terminate()
                self.process.join()

    

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
    def __init__(self, manager=None):
        if manager is None:
            manager = multiprocessing.Manager()
        self._queue = manager.Queue()  # Truly shared queue
        self._size = manager.Value('i', 0)  # Shared size counter
        self._lock = manager.Lock()
        
    @property
    def queue(self):
        return self._queue
    
    @property
    def size(self):
        return self._size
    
    def put(self, msg):
        # Atomic put operation
        self._queue.put(msg)
        with self._lock:
            self._size.value += 1
            
    def get(self, timeout=None):
        try:
            # Try to get a message
            msg = self._queue.get(timeout=timeout)
            # Update size counter atomically
            with self._lock:
                self._size.value = max(0, self._size.value - 1)
            return msg
        except q.Empty:
            raise
    
    def get_nowait(self):
        try:
            msg = self._queue.get_nowait()
            with self._lock:
                self._size.value = max(0, self._size.value - 1)
            return msg
        except q.Empty:
            raise
    
    def is_empty(self):
        with self._lock:
            return self._size.value == 0
@dataclass
class NodeState:
    node_id: str
    active: int
    device_state: Dict[str, Any]
    process_state: Dict[str, Any]



# TODO: implement removing channels (node_ids) as devices get dropped from devicelist
# similar implementation to send/receive calling transceiver functions
class SimulationTransceiver(AbstractTransceiver):

    def __init__(self, active: multiprocessing.Value, parent_id: int = None):  # type: ignore
        self._outgoing_channels = {}  # hashmap between node_id and Queue (channel)
        self._incoming_channels = {}
        #self.parent = parent
        self.parent_id = parent_id
        self._active_value = active.value if active else 2
        self.active = None  # Will be initialized in new process  # type: ignore (can activate or deactivate device with special message)
        self.logQ = deque()
        print(f"DEBUG: Creating transceiver for device {parent_id}")
        print(f"DEBUG: Outgoing channels: {list(self._outgoing_channels.keys())}")
        print(f"DEBUG: Incoming channels: {list(self._incoming_channels.keys())}")

    @property
    def outgoing_channels(self):
        return self._outgoing_channels

    @property
    def incoming_channels(self):
        return self._incoming_channels

    def __getstate__(self):
        return {
            'parent_id': self.parent_id,
            'active_value': self._active_value,
            'outgoing_channels': self._outgoing_channels,
            'incoming_channels': self._incoming_channels
        }

    def __setstate__(self, state):
        self._outgoing_channels = state['outgoing_channels']
        self._incoming_channels = state['incoming_channels']
        self.parent_id = state['parent_id']
        self._active_value = state['active_value']
        self.active = multiprocessing.Value('i', self._active_value)
        self.logQ = deque()

    def log(self, data: str):
        """ Method for protocol to load aux data into transceiver """
        self.logQ.appendleft(data)

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
        try:
            data = self.logQ.pop()
            if data:
                try:
                    asyncio.run(self.notify_server(f"{data},{self.parent_id}"))
                except OSError: 
                    pass
        except IndexError:  # empty logQ
            pass
        print(f"DEBUG: Sending message to {self.outgoing_channels.keys()}")

        for id, queue in self.outgoing_channels.items():
            if queue is not None:
                queue.put(msg)
                print(f"DEBUG: Message sent to {id}")
                # print("msg", msg, "put in device", id)
        # no need to wait for this task to finish before returning to protocol
        try:
            asyncio.run(self.notify_server(f"SENT,{self.parent_id}"))
        except OSError:
            pass
    
    def receive(self, timeout: float) -> int | None:  # get from all queues
        print(f"DEBUG: Device {self.parent_id} attempting to receive with timeout={timeout}")

        if self.active_status() == 0:
            print("returning DEACTIVATE")
            return Message.DEACTIVATE  # indicator for protocol
        if self.active_status() == 1:  # can change to Enum
            self.stay_active()
            return Message.ACTIVATE
        # print(self.incoming_channels.keys())
        end_time = time.time() + timeout #changing from per-queue timeout to overall wall timeout.
        # Capture state before consuming message for checkpoints
                        
                            
        try:
            # First try to get messages without blocking
            for device_id, queue in self._incoming_channels.items():
                try:
                    msg = queue.get_nowait()
                    print(f"DEBUG:{self.parent_id} device received this message {msg} from device {device_id}")
                    return msg
                except q.Empty:
                    continue
            
            # If no immediate messages, wait for the timeout period
            start_time = time.time()
            while time.time() - start_time < timeout:
                for device_id, queue in self._incoming_channels.items():
                    if hasattr(self.parent_id, 'checkpoint_mgr'):  #TODO: use actual node object
                            print(f"DEBUG: Capturing pre-receive state for queue {id}")
                            self.parent_id.checkpoint_mgr.create_checkpoint(
                                f"pre_receive_{id}",
                                {str(self.parent_id): self.parent_id}
                            )
                    try:
                        # Try each queue with a small timeout
                        msg = queue.get(timeout=0.1)
                        print(f"DEBUG:Device {self.parent_id} Received message {str(msg)} from device {device_id}")
                        try:
                            asyncio.run(self.notify_server(f"RCVD,{self.parent_id}"))
                        except OSError:
                            pass
                        return msg
                    except q.Empty:
                        continue
                time.sleep(0.01)  # Small sleep to prevent busy waiting
            
            print('No messages received')
            return None
            
        except Exception as e:
            print(f"DEBUG: Error in receive: {e}")
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

    async def notify_state_change(self, old_state, new_state):
        """Log state transitions for visualization"""
        message = {
            'device_id': self.parent_id,
            'old_state': old_state,
            'new_state': new_state,
            'timestamp': time.time()
        }
        await self.notify_server(f"STATE_CHANGE,{json.dumps(message)}")

    async def handle_tiebreaker(self, other_id):
        """Log tiebreaker events for visualization"""
        message = {
            'device_id': self.parent_id,
            'other_id': other_id,
            'type': 'TIEBREAKER',
            'timestamp': time.time()
        }
        await self.notify_server(f"TIEBREAKER,{json.dumps(message)}")
    # websocket client to connect to server.js and interact with injections
    async def websocket_client(self):
        uri = "ws://localhost:3000"  # server.js websocket server
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
    
            
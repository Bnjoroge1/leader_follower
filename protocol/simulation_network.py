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

def device_process_function(device_id: int, node_id: int, active_value: int):
    """Standalone function for the device process"""
    try:
        # Create fresh active value
        active = multiprocessing.Value('i', active_value)
        
        # Create fresh transceiver without parent reference
        transceiver = SimulationTransceiver(parent=None, active=active)
        transceiver.parent_id = node_id  # Store just the ID
        
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
        self.transceiver = SimulationTransceiver(parent=self, active=active)
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
    def __init__(self):
        self.queue = multiprocessing.Queue()
        self.size = multiprocessing.Value('i', 0, lock=True)  # shared value with lock for size

    def put(self, msg):
        self.queue.put(msg)
        with self.size.get_lock():
            self.size.value += 1

    def get(self, timeout=None):
        msg = self.queue.get(timeout=timeout)
        with self.size.get_lock():
            self.size.value -= 1
        return msg

    def get_nowait(self):
        msg = self.queue.get_nowait()
        with self.size.get_lock():
            self.size.value -= 1
        return msg

    def get_size(self):
        with self.size.get_lock():
            return self.size.value

    def is_empty(self):
        with self.size.get_lock():
            return self.size.value == 0

    def empty(self):
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except q.Empty:
                break
@dataclass
class NodeState:
    node_id: str
    active: int
    device_state: Dict[str, Any]
    process_state: Dict[str, Any]


# TODO: implement removing channels (node_ids) as devices get dropped from devicelist
# similar implementation to send/receive calling transceiver functions
class SimulationTransceiver(AbstractTransceiver):

    def __init__(self, parent: SimulationNode, active: multiprocessing.Value):  # type: ignore
        self.outgoing_channels = {}  # hashmap between node_id and Queue (channel)
        self.incoming_channels = {}
        self.parent = parent
        self.parent_id = None 
        self.active: multiprocessing.Value = active  # type: ignore (can activate or deactivate device with special message)
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
                    asyncio.run(self.notify_server(f"{data},{self.parent.node_id}"))
                except OSError:
                    pass
        except IndexError:  # empty logQ
            pass

        for id, queue in self.outgoing_channels.items():
            if queue is not None:
                queue.put(msg)
                # print("msg", msg, "put in device", id)
        # no need to wait for this task to finish before returning to protocol
        try:
            asyncio.run(self.notify_server(f"SENT,{self.parent.node_id}"))
        except OSError:
            pass

    def receive(self, timeout: float) -> int | None:  # get from all queues
        if self.active_status() == 0:
            print("returning DEACTIVATE")
            return Message.DEACTIVATE  # indicator for protocol
        if self.active_status() == 1:  # can change to Enum
            self.stay_active()
            return Message.ACTIVATE
        # print(self.incoming_channels.keys())
        end_time = time.time() + timeout #changing from per-queue timeout to overall wall timeout.
        for id, queue in self.incoming_channels.items():
            try:
                # Check if there's a message without consuming it
                if not queue.queue.empty():
                    # Capture state before consuming message
                    if hasattr(self.parent, 'checkpoint_mgr'):
                        print(f"DEBUG: Capturing pre-receive state for queue {id}")
                        self.parent.checkpoint_mgr.create_checkpoint(
                            f"pre_receive_{id}",
                            {str(self.parent.node_id): self.parent}
                        )
                msg = queue.get_nowait()  #Non-blocking get - basically same as get(False)
                print("Message", msg, "gotton from device", id, "waited", timeout, "seconds")
                try:
                    asyncio.run(self.notify_server(f"RCVD,{self.parent.node_id}"))
                except OSError:
                    pass
                return msg
            except q.Empty:
                pass
            time.sleep(0.01) #sleep for 10ms to avoid busy-waiting
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

    # websocket client to connect to server.js and interact with injections
    async def websocket_client(self):
        uri = "ws://localhost:3000"  # server.js websocket server
        async with websockets.connect(uri) as websocket:
            await websocket.send(f"CONNECTED,{self.parent.node_id}")  # initial connection message

            async for message in websocket:
                if isinstance(message, bytes):
                    message = message.decode("utf-8")
                print(f"Received message: {message}")
                if message == "Toggle Device":
                    print("Toggling device")
                    if self.active_status() == 0:  # been off
                        self.reactivate()  # goes through process to full activation
                        await websocket.send(f"REACTIVATED,{self.parent.node_id}")  # reactivation
                    else:
                        self.deactivate()  # recently just turned on
                        await websocket.send(f"DEACTIVATED,{self.parent.node_id}")  # deactivation

    # called via asyncio from a synchronous environment - send, receive
    async def notify_server(self, message: str):
        uri = "ws://localhost:3000"  # server.js websocket server
        async with websockets.connect(uri) as websocket:
            await websocket.send(message)
    
            
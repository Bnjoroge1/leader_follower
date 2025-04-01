import paho.mqtt.client as mqtt
import json
#from abstract_network import AbstractTransceiver, AbstractNode
import multiprocessing
import device_classes as dc
from queue import Queue
import time
import asyncio
from message_classes import Action
from ui_device import UIDevice

class ZigbeeNode():
     
    def __init__(self, node_id, active: multiprocessing.Value = None, ip= '192.168.68.89', target_func = None, target_args = None):  # type: ignore
        self.node_id = node_id
        self.active = active
        self.transceiver = ZigbeeTransceiver(broker_address=ip, broker_port=1883, active=self.active, parent = self)  # address and port subject to change
        self.thisDevice = dc.ThisDevice(self.node_id, self.transceiver)
        #self.setup(node_id, target_func, target_args, active)
        
        #self.process = multiprocessing.Process(target=self.thisDevice.device_main)
        
    def start(self):
        #self.process.start()
        new_active = multiprocessing.Value('i', self.active.value)
        device_state = {
            'id': self.thisDevice.id,
            'leader': self.thisDevice.leader,
            'received': self.thisDevice.received,
            'missed': self.thisDevice.missed,
            'task': self.thisDevice.task,
            'active': True
        }
        
        
        self.thisDevice.device_main()

class ZigbeeUINode(ZigbeeNode):
    def __init__(self, node_id=-1, active: multiprocessing.Value = None, ip= '192.168.68.89', target_func = None, target_args = None):
        self.node_id = node_id
        self.active = active
        self.transceiver = ZigbeeTransceiver(
            broker_address=ip,
            broker_port=1883,
            active=self.active,
            parent=self,
            use_mock=True  # Use mock for UI testing
        )
        self.thisDevice = UIDevice(self.node_id, self.transceiver)  # type: ignore

class MockMQTTClient:
    def __init__(self, api_version=None):
        self.on_connect = None
        self.on_message = None
        self.on_subscribe = None
        self.on_unsubscribe = None
        self.on_publish = None
        print("Mock MQTT client created")
        
    def user_data_set(self, data):
        self.user_data = data
        
    def connect(self, host, port, keepalive=60):
        print(f"Mock connecting to {host}:{port}")
        # Simulate successful connection
        if self.on_connect:
            class MockRC:
                is_failure = False
            self.on_connect(self, self.user_data, {}, MockRC(), {})
        
    def loop_start(self):
        print("Mock MQTT loop started")
        
    def loop_stop(self):
        print("Mock MQTT loop stopped")
        
    def disconnect(self):
        print("Mock MQTT disconnected")
        
    def subscribe(self, topic):
        print(f"Mock subscribed to {topic}")
        if self.on_subscribe:
            class MockRC:
                is_failure = False
            self.on_subscribe(self, self.user_data, 1, [MockRC()], {})
        
    def publish(self, topic, payload, qos=0):
        print(f"Mock publishing to {topic}: {payload}")
        class MockMsgInfo:
            def __init__(self):
                self.mid = 1
            def wait_for_publish(self):
                if self.on_publish:
                    self.on_publish(self, self.user_data, self.mid, 0, {})
                return True
        return MockMsgInfo()

class ZigbeeTransceiver():
    
    def __init__(self, broker_address='192.168.68.89', broker_port=1883, active: multiprocessing.Value = None, parent: ZigbeeNode = None, username=None, password=None, use_mock=False):
        self.active = active
        self.parent = parent
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.username = username
        self.password = password

        if use_mock:
            self.sub_client = MockMQTTClient()
            self.pub_client = MockMQTTClient()
            print("Using MockMQTTClient for testing")
        else:
            self.sub_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.pub_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            
        self.sub_topic = 'zigbee2mqtt/bridge/request/device/permit_join'
        self.rcv_queue = Queue()
        self.unacked = set()

        if username and password:
            self.sub_client.username_pw_set(username, password)
            self.pub_client.username_pw_set(username, password)
        
        # sub loop callback funcs
        self.sub_client.on_connect = self.on_sub_connect
        self.sub_client.on_subscribe = self.on_subscribe
        self.sub_client.on_unsubscribe = self.on_unsubscribe
        self.sub_client.on_message = self.on_message
        
        # start sub loop
        self.sub_client.user_data_set(self.rcv_queue)
        self.sub_client.connect(self.broker_address, self.broker_port)
        #print("here")
        self.sub_client.loop_start()  # Start the loop in a separate thread

        # start pub loop
        self.pub_client.user_data_set(self.unacked)
        self.pub_client.on_publish = self.on_pub
        self.pub_client.connect(self.broker_address, self.broker_port)
        self.pub_client.loop_start()  # Start the loop in a separate thread
    
    def deactivate(self):
        self.active.value = 0
    
    def reactivate(self):
        self.active.value = 1
        
    def stay_active(self):
        self.active.value = 2
        
    def active_status(self):
        return self.active.value
        
    def send(self, msg, topic='zigbee2mqtt/bridge/request/device/permit_join'):
        # Convert the message to JSON if it's a dictionary
        if isinstance(msg, dict):
            msg = json.dumps(msg)
        
        # Publish the message to the specified topic
        # qos=1 waits for acknowledgement from broker  (we could do 0 which has no wait)
        msg_info = self.pub_client.publish(topic, msg, qos=1)
        self.unacked.add(msg_info.mid)
        msg_info.wait_for_publish()
        # rc is at index 0 of msg_info - will be 0 if success
        # we could use this to decide whether we should resend or not?
    
    def receive(self, timeout):
        if self.active_status() == 0:
            return Action.DEACTIVATE.value
        if self.active_status() == 1:
            self.stay_active()
            return Action.ACTIVATE.value
        # sub client is already subscribed, we just wait for queue to receive
        end = time.time() + timeout
        msg = None
        while time.time() < end:
            if not self.rcv_queue.empty():
                msg = int(self.rcv_queue.get())
                break
        #print(self.rcv_queue.qsize())  
 
        return msg

    def __del__(self):
        self.sub_client.loop_stop()  # Stop the loop when the object is deleted
        self.sub_client.disconnect()
        self.pub_client.loop_stop()  # Stop the loop when the object is deleted
        self.pub_client.disconnect()

    def on_message(self, client, userdata, message):
        # we want to put any message received since protocol will
        # handle whether it is valid or not
        # we could change this setup to allow for checks here which may be faster
        #print(int(message.payload))
        self.rcv_queue.put(message.payload)

    def on_sub_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            print(f"failure {reason_code}")
        else:
            client.subscribe(self.sub_topic)
            
    def on_subscribe(self, client, userdata, mid, reason_list, properties):
        if reason_list[0].is_failure:
            print(f"failed: {reason_list[0]}")
        else:
            print("suback")
    def on_unsubscribe(self, client, userdata, mid, reason_list, properties):
        print('unsub')
        client.disconnect()
        
    def on_pub(self, client, userdata, mid, reason_code, properties):
        try:
            #print(mid)
            userdata.remove(mid)
        except KeyError:
            print("race condition occurred")
        except:
            print("other error ocurred")


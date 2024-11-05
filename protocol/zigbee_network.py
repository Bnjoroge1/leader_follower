import paho.mqtt.client as mqtt
import json
from abstract_network import AbstractTransceiver, AbstractNode
import multiprocessing
import device_classes as dc


class ZigbeeNode(AbstractNode):
     
    def __init__(self, node_id, target_func = None, target_args = None, active: multiprocessing.Value = None):  # type: ignore
        self.transceiver = ZigbeeTransceiver(broker_address='localhost', broker_port=1883)  # address and port subject to change
        self.setup(node_id, target_func, target_args, active)


class ZigbeeTransceiver(AbstractTransceiver):
    
    def __init__(self, broker_address='localhost', broker_port=1883, username=None, password=None):
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.client = mqtt.Client()
        
        if username and password:
            self.client.username_pw_set(username, password)
        
        self.client.connect(self.broker_address, self.broker_port)
        self.client.loop_start()  # Start the loop in a separate thread

    def send(self, msg, topic='zigbee2mqtt/bridge/request/device/permit_join'):
        # Convert the message to JSON if it's a dictionary
        if isinstance(msg, dict):
            msg = json.dumps(msg)
        
        # Publish the message to the specified topic
        self.client.publish(topic, msg)

    def __del__(self):
        self.client.loop_stop()  # Stop the loop when the object is deleted
        self.client.disconnect()
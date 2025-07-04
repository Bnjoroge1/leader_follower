from abstract_network import AbstractNode, AbstractTransceiver
import device_classes as dc
import socket
from typing import AnyStr, Dict
from collections import defaultdict

class VMNetworkAddressMap():
     def __init__(self):
          self.address_map: Dict[int, str] = defaultdict(lambda: "127.0.0.1")

     def get_address_from_node(self, node_id: int):
          return self.address_map.get(node_id, "127.0.0.1")
     
     def set_address_from_node(self, node_id:int, ip_address:str):
          self.address_map[node_id] = ip_address
     



class VMNetworkTransceiver(AbstractTransceiver):
     def __init__(self,node_id, address_map, ip_addr, port):
          self.addresss_map =  address_map
          self.channel = socket.socket(socket.AF_INET,socket.SOCK_DGRAM ) #initializing a socket conenction that will be used to send messages. 
          self.channel.bind(ip_addr, port)  #binding port to socket
          print(f"Initialized transceiver {self.node_id}. Listening on {ip_addr}")


     

     def send(self, node_id, message:int , addr):
          #get the ip address for this node
          ip_address = self.addresss_map.get(node_id)
          message_bytes = message.to_bytes()
          if ip_address:
               self.channel.send(str(message))







class VMNode():
     def __init__(self, node_id:int, active_value:int, target_func, ip_address):
          self.node_id = node_id
          self.active_value = active_value
          self.target_func=target_func
          self.ip_address=ip_address
          self.transceiver = VMNetworkTransceiver(ip_address)
          self.thisDevice = dc.thisDevice()


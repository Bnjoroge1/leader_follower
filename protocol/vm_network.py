from abstract_network import AbstractNode, AbstractTransceiver
import device_classes as dc
import socket
from typing import Any, AnyStr, Dict, Optional
from collections import defaultdict
import asyncio

class VMNetworkAddressMap():
     def __init__(self):
          self.address_map: Dict[int, tuple] = defaultdict(lambda: ("127.0.0.1", 8001))

     def get_address_from_node(self, node_id: int):
          return self.address_map.get(node_id, ("127.0.0.1", 8001))
     
     def set_address_from_node(self, node_id:int, ip_address:tuple):
          self.address_map[node_id] = ip_address
class VMNetworkUDP(asyncio.DatagramProtocol):
     def __init__(self) -> None:
          super().__init__()
          self.transport = None
          self.receive_queue = asyncio.Queue()    

     def connection_made(self, transport: asyncio.DatagramTransport) -> None:
          self.transport = transport
          print("UDP endpoint ready and lisening")
     def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
          print(f"received {bytes.decode("utf-8")}")
          self.receive_queue.put_nowait(data)
     def connection_lost(self, exc: Exception | None) -> None:
          self.transport.close()


class VMNetworkTransceiver(AbstractTransceiver):
     def __init__(self, node_id, address_map:VMNetworkAddressMap):
          self.address_map:VMNetworkAddressMap =  address_map
          self.node_id = node_id

          self.transport: Optional[asyncio.DatagramTransport] = None
          self.receive_queue: Optional[asyncio.Queue] = None
          print(f"Initialzed empty transceiver for {self.node_id}")
     def send(self, msg):
        pass
     def receive(self):
          pass

     def async_send(self, destination_id:int,  msg: int) -> None:
          if not self.transport:
               print(f"ERROR: Transceiver for {self.node_id} cannot send.")
               return
          full_address = self.address_map.get_address_from_node(destination_id)
          if not full_address:
               print(f"Error: No address found for node{self.node_id}")        
          message_bytes = msg.to_bytes(6, byteorder="big")

          #use the transport objct to actually send
          self.transport.sendto(message_bytes, full_address)

     async def async_receive(self, timeout: float) -> Optional[int]:
          print("receivng stuff")
          if not self.receive_queue:
               print(f"Receive queue for {self.node_id} does no exist.")

          try:
               data = await asyncio.wait_for(self.receive_queue.get(), timeout=timeout)
               return int.from_bytes(data, byteorder="big")
          except asyncio.TimeoutError:
               return None
     
               







class VMNode():
     def __init__(self, node_id:int, ip_address:str, port:int,   address_map:VMNetworkAddressMap):
          self.node_id = node_id
          self.ip_address=ip_address
          self.port = port
          #self.hostname = hostname 
          self.address_map:VMNetworkAddressMap = address_map
          self.transceiver = VMNetworkTransceiver(node_id,address_map)
          self.thisDevice = dc.ThisDevice(self.__hash__() % 10000, self.transceiver)
     
     async def start(self):
          print(f"VMNode {self.node_id} starting its device logic.")
          print('Starting UDP server')
          loop = asyncio.get_running_loop()
          transport, protocol = await loop.create_datagram_endpoint(
          lambda:VMNetworkUDP(), 
          local_addr=(self.ip_address, self.port)
          )
          self.transceiver.transport = transport
          self.transceiver.receive_queue = protocol.receive_queue
          
          await self.thisDevice.device_main()

     def __str__(self) -> str:
         return f"Node with node id: {self.node_id} \
         HostName: , IP Address: {self.ip_address.split(':')[0]}" \
         ""
               
                    

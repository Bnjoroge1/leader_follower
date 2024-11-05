from abstract_driver import AbstractDriver
import asyncio
from zigbee_network import ZigbeeTransceiver, ZigbeeNode
import device_classes as dc

class ZigbeeDriver(AbstractDriver):

    async def main(self):
        node = ZigbeeNode()  # takes care of channel setup and looping (non-blocking)

        # all UI comms will take place over Zigbee, websocket not necessary
        
        node.start()
        
    async def test():
        node = ZigbeeNode()

        # Send a message to permit joining new devices
        node.transceiver.send({"value": "true"}, topic='zigbee2mqtt/bridge/request/device/permit_join')

        # Send a custom message to a specific device
        node.transceiver.send({"state": "ON"}, topic='zigbee2mqtt/my_device/set')


if __name__ == "__main__":
    driver = ZigbeeDriver()
    # asyncio.run(driver.test())
    asyncio.run((driver.main()))
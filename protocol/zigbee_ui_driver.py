#from abstract_driver import AbstractDriver
import time
import asyncio
from uuid import getnode
from zigbee_network import ZigbeeTransceiver, ZigbeeUINode
import device_classes as dc
import multiprocessing

class ZigbeeDriver():

    async def main(self):
        try:
            self.mac_id = getnode() % 10000
            shared_active = multiprocessing.Value('i', 1)
            node = ZigbeeUINode(self.mac_id, active= shared_active, ip='localhost')  # takes care of channel setup and looping (non-blocking)

            # all UI comms will take place over Zigbee, websocket not necessary
            print("Starting 5 second countdown to position robot!")
            end = time.time() + 5
            while time.time() < end:
                print(f"Time remaining: {int(end - time.time())} seconds")
                await asyncio.sleep(1)
                
            print("Starting UI node...")
            # Use try/except to catch and log any errors during startup
            try:
                node.start()
            except Exception as e:
                print(f"Error in node.start(): {e}")
                import traceback
                traceback.print_exc()
        except Exception as e:
            print(f"Error in main: {e}")
            import traceback
            traceback.print_exc()
        
    async def test():
        node = ZigbeeUINode()

        # Send a message to permit joining new devices
        node.transceiver.send({"value": "true"}, topic='zigbee2mqtt/bridge/request/device/permit_join')

        # Send a custom message to a specific device
        node.transceiver.send({"state": "ON"}, topic='zigbee2mqtt/my_device/set')


if __name__ == "__main__":
    driver = ZigbeeDriver()
    # asyncio.run(driver.test())
    asyncio.run(driver.main())

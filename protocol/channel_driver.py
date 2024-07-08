import time
from simulation_network import SimulationNode, NetworkVisualizer, Network
from multiprocessing import Value
import itertools
import asyncio
from copy import copy

async def main():
    """
    Main driver for protocol simulation.
    :return:
    """
    # startup
    num_devices = 5
    network = Network()
    nodes = []
    init_tasks = []
    for i in range(num_devices):
        shared_active = Value('i', 2)  # 0 == off, 1 == just reactivated, 2 == active
        new_node = SimulationNode(i+1, active=shared_active)  # can we move active to lower level like size?
        nodes.append(new_node)
        init_tasks.append(new_node.async_init())
        network.add_node(new_node.node_id, new_node)

    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            firstNode = nodes[i]
            secondNode = nodes[j]
            print("CHANNEL SETUP", firstNode.node_id, secondNode.node_id)
            network.create_channel(firstNode.node_id, secondNode.node_id)

    visualizer = NetworkVisualizer()
    visualizer.ui_main()

    for node in nodes:
        node.start()
        time.sleep(5)

    await asyncio.gather(*init_tasks)


if __name__ == "__main__":
    asyncio.run(main())

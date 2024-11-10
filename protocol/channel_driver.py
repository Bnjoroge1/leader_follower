import time
from simulation_network import SimulationNode, NetworkVisualizer, Network
from multiprocessing import Value
import itertools
import asyncio
from copy import copy
import argparse
from checkpoint_manager import CheckpointManager

def parse_args():
    parser = argparse.ArgumentParser(description='Protocol Simulation Driver')
    parser.add_argument('-t', '--trace', 
                       nargs='*',
                       default=[],
                       help='Enable trace points. Examples: -t BECOMING_FOLLOWER HANDLING_DLIST')
    parser.add_argument('-c', '--checkpoint-dir',
                       default='checkpoints',
                       help='Directory to store checkpoints')
    parser.add_argument('-r', '--restore',
                       help='Restore from checkpoint file. Use "latest" for most recent checkpoint')
    parser.add_argument('-l', '--list-checkpoints',
                       action='store_true',
                       help='List available checkpoints')
    return parser.parse_args()

async def main():
    """
    Main driver for protocol simulation.
    :return:
    """
    args = parse_args()
    checkpoint_mgr = CheckpointManager(args.checkpoint_dir)
    if args.list_checkpoints:
        checkpoints = checkpoint_mgr.list_checkpoints()
        print(f"Available checkpoints: ")
        for cp in checkpoints:
            print(f"    {cp}")
        return
    
    if args.restore:
        checkpoint_path = args.restore
        if checkpoint_path.lower() == "latest":
            checkpoint_path = checkpoint_mgr.get_latest_checkpoint()
            if not checkpoint_path:
                print("No checkpoints available")
                return
        print(f"Restoring from checkpoint: {checkpoint_path}")
        checkpoint_data = checkpoint_mgr.restore_checkpoint(checkpoint_path)
        print("DEBUG: Checkpoint message queues during restore:", checkpoint_data.message_queues)

        # Create network with restored state
        network = Network()
        nodes = []
        init_tasks = []
        # First create all nodes without restoring state
        for node_id, node_state in checkpoint_data.node_states.items():
            shared_active = Value('i', node_state.get('active', 2))
            new_node = SimulationNode(
                node_id=node_id, 
                active=shared_active,
                checkpoint_mgr=checkpoint_mgr
            )
            nodes.append(new_node)
            network.add_node(node_id, new_node)

        # Create all channels first
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                firstNode = nodes[i]
                secondNode = nodes[j]
                print("CHANNEL SETUP", firstNode.node_id, secondNode.node_id)
                network.create_channel(firstNode.node_id, secondNode.node_id)
                print(f"DEBUG: Created channel between {firstNode.node_id} and {secondNode.node_id}")
                print(f"DEBUG: First node channels: {firstNode.transceiver.incoming_channels.keys()}")
                print(f"DEBUG: Second node channels: {secondNode.transceiver.incoming_channels.keys()}")

        # Restore nodes from checkpoint
        for node in nodes:
            node_state = checkpoint_data.node_states[node.node_id]
            print(f"DEBUG: Restoring node {node.node_id} with state before restore: {node_state}")
            queue_state = checkpoint_data.message_queues.get(str(node.node_id), {})
            node.restore_from_checkpoint(
                node_state, 
                queue_state
            )
            print(f"DEBUG: Node channels after restore: {node.transceiver.incoming_channels.keys()}")

            init_tasks.append(node.async_init())


        # Start visualization and nodes
        visualizer = NetworkVisualizer()
        visualizer.ui_main()
        started_tasks = [asyncio.create_task(task) for task in init_tasks]
        print("started tasks", started_tasks)

        for node in nodes:
            time.sleep(5)  # intentional synchronous delay
            node.start()
        

    
    else: 
        if args.trace:
            for point in args.trace:
                checkpoint_mgr.enable_trace(point)
        # startup
        num_devices = 4
        network = Network()
        nodes = []
        init_tasks = []
        for i in range(num_devices):
            shared_active = Value('i', 2)  # 0 == off, 1 == just reactivated, 2 == active
            new_node = SimulationNode(i+1, active=shared_active, checkpoint_mgr=checkpoint_mgr)  # can we move active to lower level like size?
            nodes.append(new_node)
            init_tasks.append(new_node.async_init())  # prepare async initialization tasks
            network.add_node(new_node.node_id, new_node)

        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                firstNode = nodes[i]
                secondNode = nodes[j]
                print("CHANNEL SETUP", firstNode.node_id, secondNode.node_id)
                network.create_channel(firstNode.node_id, secondNode.node_id)

        visualizer = NetworkVisualizer()
        visualizer.ui_main()
        # starts each task - connects websockets to server..js before protocol starts
        started_tasks = [asyncio.create_task(task) for task in init_tasks]
        print("started tasks", started_tasks)

        for node in nodes:
            time.sleep(5)  # intentional synchronous delay
            node.start()

        # indefinitely awaiting websocket tasks
        try:
            await asyncio.gather(*started_tasks)
            assert False  # making sure websockets have not stopped
        except OSError:
            await asyncio.Event().wait()

        
if __name__ == "__main__":
    asyncio.run(main())

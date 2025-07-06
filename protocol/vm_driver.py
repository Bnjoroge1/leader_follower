import asyncio
import argparse
from vm_network import VMNetworkAddressMap, VMNode
import json



async def main():
    # 1. Define and parse arguments correctly
    parser = argparse.ArgumentParser(description='VM Protocol Node Driver')
    parser.add_argument('--node-id', required=True, type=int, help="The unique ID for this node.")
    parser.add_argument('--config', default='config.json', help="Path to the network configuration file.")
    args = parser.parse_args()

    # 2. Load configuration from the specified file
    print(f"Loading configuration from {args.config} for node {args.node_id}")
    with open(args.config, 'r') as f:
        config_data = json.load(f)

    # 3. Correctly populate the address map
    address_map = VMNetworkAddressMap()
    nodes_config = config_data.get("nodes", {})
    node_ids = []
    for node_id_str, address_str in nodes_config.items():
        node_id_int = int(node_id_str)
        node_ids.append(node_id_int)
        ip, port_str = address_str.split(':')
        port_int = int(port_str)
        address_map.set_address_from_node(node_id_int, (ip, port_int))
    
    print("Address map populated:")
    for node_id, addr in address_map.address_map.items():
        print(f"  Node {node_id} -> {addr[0]}:{addr[1]}")

    # 4. Identify this node's own address
    my_address = address_map.get_address_from_node(args.node_id)
    if not my_address:
        print(f"FATAL: Node ID {args.node_id} not found in configuration file.")
        return

    my_ip, my_port = my_address

    # 5. Instantiate the VMNode with all required arguments
    print(f"Initializing VMNode {args.node_id} to run at {my_ip}:{my_port}")
    current_node = VMNode(
        node_id=args.node_id,
        ip_address=my_ip,
        port=my_port,
        address_map=address_map  # Pass the complete map!
    )
     print("Priming device list with all known nodes from config...")
     for node_id in node_ids:
        # We use add_device to create a placeholder Device object for each participant.
        # Task index can be 0 as it's unassigned.
        await current_node.thisDevice.device_list.add_device(id=node_id, task_index=0, thisDeviceId=current_node.thisDevice.id)
    
     print("Initial Device List:")
     print(current_node.thisDevice.device_list)
     # 6. Start the node's main logic
     await current_node.start()

if __name__ == "__main__":
    print("Starting VM Node Driver...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down driver.")
    except FileNotFoundError:
        print("\nFATAL: Could not find config.json. Please create it.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
          
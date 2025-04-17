from multiprocessing import Queue
from pathlib import Path
import queue
import time
from simulation_network import SimulationNode, NetworkVisualizer, Network, SimulationTransceiver
import multiprocessing
import itertools
import asyncio
from copy import copy
import argparse
from checkpoint_manager import CheckpointManager
from ui_device import UIDevice
import logging



from aiohttp import web
import aiohttp_cors 
import traceback 
# --- Store nodes globally or pass to handlers ---
# Simplest way for example: make nodes accessible within main scope
# A better approach might involve classes or app context
simulation_nodes_map: dict[int, SimulationNode] = {}
CURRENT_FILE = Path(__file__).absolute()
PROTOCOL_DIR = CURRENT_FILE.parent
OUTPUT_DIR = PROTOCOL_DIR / "output"
global_ui_update_queue: multiprocessing.Queue 


def listener_configure():
    #configure root logger
    root = logging.getLogger()
    log_path = OUTPUT_DIR / "simulation.log"
    fh = logging.FileHandler(log_path, mode='w')
    formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(message)s', datefmt='%Y-%m-%d %H:%M:%S.%f')
    fh.setFormatter(formatter)
    root.addHandler(fh)
    root.setLevel(logging.DEBUG)
def listener_process(log_queue: multiprocessing.Queue, configurer):
    """Runs in a separate process to listen for log records."""
    configurer()
    listener = logging.handlers.QueueListener(log_queue, logging.getLogger(), respect_handler_level=True)
    listener.start()
    try:
        # Keep listener running until sentinel (None) is received
        while True:
            record = log_queue.get()
            if record is None: # Sentinel value to stop
                break
            # QueueListener handles the record processing internally now
            # logger = logging.getLogger(record.name)
            # logger.handle(record) # No longer needed with QueueListener
    except Exception as e:
        print(f"Logging listener error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        listener.stop()
        print("Logging listener stopped.")         


# --- Define HTTP Handlers ---
async def handle_stop_device(request):
    device_id_str = request.match_info.get('device_id', None)
    if not device_id_str:
        return web.Response(status=400, text="Missing device_id")
    try:
        device_id = int(device_id_str)
        node_to_stop = simulation_nodes_map.get(device_id)
        if node_to_stop:
            print(f"API: Stopping node {device_id}")

            #log the data to the UI
            # add to the queue first
            global global_ui_update_queue
            if global_ui_update_queue:
                if node_to_stop.thisDevice.leader:
                    log_data = {"level": "WARN", "message": f"Leader node: {device_id} stopped. Triggerring leader election."}     
                log_data = {"level": "WARN", "message": f"API Node: {device_id} stopping"}
                global_ui_update_queue.put(("log_event", log_data))  


            if hasattr(node_to_stop, 'stop') and callable(node_to_stop.stop):
                node_to_stop.stop()
                    # Update UI device list with active=false for this device
                if 'ui_device' in globals() and isinstance(globals()['ui_device'], UIDevice):
                    # Get current device list
                    current_list = globals()['ui_device'].latest_device_list_cache
                    for device in current_list:
                        if device['id'] == device_id:
                                device['active'] = False  # Mark as inactive
                        
                    # Force a device list update
                    globals()['ui_device'].latest_device_list_cache = current_list
                    if global_ui_update_queue:
                        global_ui_update_queue.put(("device_list", current_list))
                return web.Response(text=f"Node {device_id} stopping.")
            else:
                 # If no stop method, maybe set active flag? Less realistic for full stop.
                 if hasattr(node_to_stop, 'active'): node_to_stop.active.value = 0 # Assuming 0 means stopped/inactive
                 return web.Response(text=f"Node {device_id} marked inactive (no stop method).")
        else:
            return web.Response(status=404, text=f"Node {device_id} not found")
    except ValueError:
        return web.Response(status=400, text="Invalid device_id format")
    except Exception as e:
        print(f"Error stopping node {device_id_str}: {e}")
        traceback.print_exc()
        return web.Response(status=500, text="Error stopping node")

async def handle_start_device(request):
    """Handles API request to start a simulation node process."""
    device_id_str = request.match_info.get('device_id', None)
    if not device_id_str:
        return web.Response(status=400, text="Missing device_id")

    try:
        device_id = int(device_id_str)
        node_to_start = simulation_nodes_map.get(device_id)

        if not node_to_start:
            return web.Response(status=404, text=f"Node {device_id} not found")

        # Check if the node has a process and if it's already running
        process_running = False
        if hasattr(node_to_start, 'process') and isinstance(node_to_start.process, multiprocessing.Process):
            if node_to_start.process.is_alive():
                process_running = True

        if process_running:
            print(f"API: Node {device_id} process is already running.")
            return web.Response(status=409, text=f"Node {device_id} process is already running.") # 409 Conflict

        # Check if the node has a start method
        if hasattr(node_to_start, 'start') and callable(node_to_start.start):
            try:
                print(f"API: Starting node {device_id}")
                #logging the start action
                global global_ui_update_queue
                if global_ui_update_queue:
                    log_data = {"level": "WARN", "message": f"{node_to_start}"}
                    global_ui_update_queue.put(("log_event", log_data))

                node_to_start.start()
                # Give it a moment to potentially start up before confirming
                await asyncio.sleep(0.5)
                # Re-check process state after attempting start
                if hasattr(node_to_start, 'process') and node_to_start.process.is_alive():
                     return web.Response(text=f"Node {device_id} started successfully.")
                else:
                     print(f"API: Node {device_id} failed to start or start method doesn't manage process correctly.")
                     return web.Response(status=500, text=f"Node {device_id} failed to start.")

            except Exception as start_exc:
                print(f"Error calling start() for node {device_id}: {start_exc}")
                traceback.print_exc()
                return web.Response(status=500, text=f"Error occurred while trying to start node {device_id}.")
        else:
            print(f"API: Node {device_id} does not have a callable 'start' method.")
            return web.Response(status=501, text=f"Node {device_id} cannot be started via API (no start method).") # 501 Not Implemented

    except ValueError:
        return web.Response(status=400, text="Invalid device_id format")
    except Exception as e:
        print(f"Error handling start request for node {device_id_str}: {e}")
        traceback.print_exc()
        return web.Response(status=500, text="Internal server error processing start request.")


async def handle_set_active_state(request, target_active_state: int):
    device_id_str = request.match_info.get('device_id', None)
    if not device_id_str:
        return web.Response(status=400, text="Missing device_id")
    try:
        device_id = int(device_id_str)
        node_to_modify = simulation_nodes_map.get(device_id)
        if node_to_modify and hasattr(node_to_modify, 'active'):
            print(f"API: Setting node {device_id} active state to {target_active_state}")
            #log data
            global global_ui_update_queue
            if global_ui_update_queue:
                 log_data = {"level": "WARN", "message": f"API: Node {device_id} stopping."}
                 global_ui_update_queue.put(("log_event", log_data))

            node_to_modify.active = target_active_state
            state_str = "active" if target_active_state == 2 else "inactive"
            return web.Response(text=f"Node {device_id} set to {state_str}.")
        elif not node_to_modify:
            return web.Response(status=404, text=f"Node {device_id} not found")
        else:
             return web.Response(status=500, text=f"Node {device_id} has no 'active' attribute.")
    except ValueError:
        return web.Response(status=400, text="Invalid device_id format")
    except Exception as e:
        print(f"Error setting active state for node {device_id_str}: {e}")
        traceback.print_exc()
        return web.Response(status=500, text="Error setting active state")

async def handle_activate_device(request):
    return await handle_set_active_state(request, 2)

async def handle_deactivate_device(request):
     # Use a different value if 0 means fully stopped vs temporarily inactive
    return await handle_set_active_state(request, 0) 

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
    parser.add_argument('--partition_sim', action='store_true', help='Run a partitioned simulation')
    return parser.parse_args()

async def process_ui_updates(ui_device: UIDevice, update_queue: Queue):
    """Task to read updates from the queue and broadcast them via WebSocket."""
    print("UI Update Processor Task started.")
    while True:
        try:
            update_type, data = update_queue.get_nowait()
            # --- Update cache if it's a device_list update ---
            if update_type == 'device_list' and isinstance(data, list):
                print(f"Main Process: Caching device_list update: {data}")
                ui_device.latest_device_list_cache = data # Store the latest list
                await ui_device.broadcast_update(update_type, data)

            # --- End cache update ---
            elif update_type == "log_event" and isinstance(data, dict):
                print(f"Main procss is processing: {data}")
                log_payload = {
                    "level": data.get("level", "INFO"),
                    "message": data.get("message", ""),
                    "type": "log_event",
                    "device_id" : "API server"
                }
                await ui_device.broadcast_update("message_log", log_payload)
                continue
            elif update_type == "message_log" and isinstance(data, dict):
                 print(f"Main Process: Processing message_log from UIDevice: {data}")
                 # The data should already be in the correct format (MessageLogData)
                 # Broadcast directly as 'message_log' type
                 print(f"DEBUG: Main Process broadcasting UIDevice log as message_log: {data}") # <-- ADD DEBUG
                 await ui_device.broadcast_update("message_log", data)

        except queue.Empty:
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error processing UI update from queue: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(1)

async def main():
    """
    Main driver for protocol simulation.
    :return:
    """
    manager = multiprocessing.Manager()
    ui_update_queue = manager.Queue()
    global global_ui_update_queue
    global_ui_update_queue = ui_update_queue  #type:ignore


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
            shared_active = multiprocessing.Value('i', node_state.get('active', 2))
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
                print(f"DEBUG: First node channels: {firstNode.transceiver.incoming_channels.keys()}")
                print(f"DEBUG: Second node channels: {secondNode.transceiver.incoming_channels.keys()}")
                print(f"DEBUG: Created channFel between {firstNode.node_id} and {secondNode.node_id}")

        # Restore nodes from checkpoint
        for node in nodes:
            node_state = checkpoint_data.node_states[node.node_id]
            print(f"DEBUG: Restoring node {node.node_id} with state before restore: {node_state}")
            queue_state = checkpoint_data.message_queues.get(str(node.node_id), {})
            node.restore_from_checkpoint(
                node_state,
                queue_state
            )
            print(f"DEBUG: Node state for {node.node_id}: {node_state}")
            print(f"DEBUG: Queue state for {node.node_id}: {queue_state}")
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

        network = Network(manager)
        nodes = []
        init_tasks = []
        for i in range(num_devices):
            shared_active = multiprocessing.Value('i', 2)  # 0 == off, 1 == just reactivated, 2 == active

            new_node = SimulationNode(i+1, active=shared_active, checkpoint_mgr=checkpoint_mgr)  # can we move active to lower level like size?
            nodes.append(new_node)
            init_tasks.append(new_node.async_init())  # prepare async initialization tasks
            network.add_node(new_node.node_id, new_node)
        #update device list

        #adding UI device
        # --- Create UIDevice Node and Instance Correctly ---
        ui_device_id = num_devices + 1
        print(f"Creating UI device node with ID {ui_device_id}")
        ui_shared_active = manager.Value('i', 2)
        #ui_update_queue = manager.Queue()

        # 1. Create the Transceiver for the UI device first
        ui_transceiver = SimulationTransceiver(active=ui_shared_active, parent_id=ui_device_id)
         # 2. Create the UIDevice instance using the transceiver
        print(f"Creating UIDevice instance for ID {ui_device_id}")
        ui_device = UIDevice(ui_device_id, ui_transceiver, ui_update_queue)
        print(f"UIDevice instance created successfully")
        ui_node = SimulationNode(
            node_id=ui_device_id, # Assign the ID here
            target_func=ui_device.device_main,     # We'll set this later
            active=ui_shared_active,
            checkpoint_mgr=checkpoint_mgr # Pass checkpoint manager if needed
        )
         # 4. Assign the UIDevice instance and transceiver back to the node
        #    (Important for state access and network setup)
        print(f"Assigning components to UI node {ui_device_id}")
        ui_node.thisDevice = ui_device
        ui_node.transceiver = ui_transceiver # Ensure the node uses the same transceiver

        # 2. Add the UI node to the network (this initializes its transceiver)
        print(f"Adding UI node {ui_device_id} to network")
        network.add_node(ui_device_id, ui_node)

       
        print(f"UI node {ui_device_id} configured successfully")
        # --- End Corrected UIDevice Creation ---
        partition_a = {1,2}
        partition_b = {3,4}
        def _is_same_partition(node_id1, node_id2 ):
            return (node_id1 in partition_a and node_id2 in partition_a) or (node_id1 in partition_b and node_id2 in partition_b)
        for i in range(len(nodes)):
                for j in range(i+1, len(nodes)):

                    firstNode = nodes[i]
                    secondNode = nodes[j]
                    if args.partition_sim:
                        firstNode = nodes[i]
                        secondNode = nodes[j]
                        if not _is_same_partition(firstNode.node_id, secondNode.node_id):
                            continue
                        print("CHANNEL SETUP", firstNode.node_id, secondNode.node_id)
                        network.create_channel(firstNode.node_id, secondNode.node_id)
                        print(f"DEBUG: First node channels: {firstNode.transceiver.incoming_channels.keys()}")
                        print(f"DEBUG: Second node channels: {secondNode.transceiver.incoming_channels.keys()}")
                        print(f"DEBUG: Created channel between {firstNode.node_id} and {secondNode.node_id} in same partition")
                    network.create_channel(firstNode.node_id, secondNode.node_id)

        # Create channels between regular devices
        # for i in range(len(nodes)):
        #     for j in range(i+1, len(nodes)):
        #         firstNode = nodes[i]
        #         secondNode = nodes[j]
        #         print("CHANNEL SETUP", firstNode.node_id, secondNode.node_id)
        #         network.create_channel(firstNode.node_id, secondNode.node_id)

        # Connect the UI device node to all other regular device nodes
        print(f"Connecting UI node {ui_device_id} to other nodes")
        for node in nodes:
            network.create_channel(ui_device_id, node.node_id)
        print(f"UI node {ui_device_id} connected")

        all_nodes = nodes + [ui_node] # Combine regular nodes and UI node
        simulation_nodes_map.clear()
        for n in all_nodes:
            if hasattr(n, 'thisDevice') and hasattr(n.thisDevice, 'id'):
                simulation_nodes_map[n.thisDevice.id] = n
                print(f"Mapping dynamic device ID to simulaation node: {getattr(n, 'node_id')}")
            print(f"could not map node {getattr(n, 'node_id')}")
            

     
      # Start the WebSocket server task using the main process's ui_device instance
        print(f"Creating WebSocket server task")
        ws_server_task = asyncio.create_task(ui_device.start_ws_server())
        print(f"WebSocket server task created: {ws_server_task}")

        # Start the task that processes updates from the UI device process queue
        print(f"Creating UI update processing task")
        ui_update_processor_task = asyncio.create_task(process_ui_updates(ui_device, ui_update_queue)) # type: ignore
        print(f"UI update processing task created: {ui_update_processor_task}")


        # starts each task - connects websockets to server..js before protocol starts
        print(f"Creating tasks for node initialization")
        started_tasks = [asyncio.create_task(task) for task in init_tasks]
        print(f"Started initialization tasks: {started_tasks}")
        print(f"WebSocket server task: {ws_server_task}")
        print(f"UI Update Processor task: {ui_update_processor_task}")

         # --- Setup HTTP Server ---
        http_app = web.Application()
        cors = aiohttp_cors.setup(http_app, defaults={
        "http://localhost:5173": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*", # Allow all standard methods including POST
            ),
        })
         # --- Add routes and apply CORS ---
        # Wrap each route registration with CORS configuration
        resource_stop = cors.add(http_app.router.add_resource('/simulate/stop/{device_id}'))
        cors.add(resource_stop.add_route("POST", handle_stop_device))

        resource_start = cors.add(http_app.router.add_resource('/simulate/start/{device_id}'))
        cors.add(resource_start.add_route("POST", handle_start_device))

        resource_activate = cors.add(http_app.router.add_resource('/simulate/activate/{device_id}'))
        cors.add(resource_activate.add_route("POST", handle_activate_device))

        resource_deactivate = cors.add(http_app.router.add_resource('/simulate/deactivate/{device_id}'))
        cors.add(resource_deactivate.add_route("POST", handle_deactivate_device))
        http_runner = web.AppRunner(http_app)
        await http_runner.setup()
        # Choose a different port for the HTTP API, e.g., 8080
        http_site = web.TCPSite(http_runner, '0.0.0.0', 8080)
        await http_site.start()
        print("HTTP Simulation Control Server started on port 8080")

        for i, node in enumerate(nodes):
            print(f"Starting node {i+1}/{len(nodes)}: {node.node_id}")
            node.start()
        print(f"Starting UI node: {ui_node.node_id}")
        ui_node.start()
        print(f"All nodes started successfully")
        # indefinitely awaiting websocket tasks
        try:
            await asyncio.gather(ws_server_task,ui_update_processor_task, *started_tasks)
            assert False  # making sure websockets have not stopped
        except OSError:
            await asyncio.Event().wait()
        finally:
            # Ensure cleanup happens even on errors if possible
            await http_runner.cleanup()


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)

    # Create manager before running main
    with multiprocessing.Manager() as manager:
        asyncio.run(main())
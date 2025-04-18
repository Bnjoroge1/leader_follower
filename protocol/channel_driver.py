from multiprocessing import Queue
from pathlib import Path
import queue
import time
from typing import Any

from blinker import ANY
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
global_ui_update_queue:Any =  asyncio.Queue


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
                await global_ui_update_queue.put(("log_event", log_data))  


            if hasattr(node_to_stop, 'stop') and callable(node_to_stop.stop):
                # Check if stop is async
                if asyncio.iscoroutinefunction(node_to_stop.stop):
                     await node_to_stop.stop()
                else:
                    # If stop is sync, run in executor to avoid blocking
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, node_to_stop.stop)
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
                        await global_ui_update_queue.put(("device_list", current_list))
                return web.Response(text=f"Node {device_id} stopping.")
            else:
                 # If no stop method, maybe set active flag? Less realistic for full stop.
                 if hasattr(node_to_stop, 'active'): node_to_stop._active_value = 0 # Assuming 0 means stopped/inactive
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
        if hasattr(node_to_start, 'start') and callable(node_to_start.start):
            try:
                print(f"API: Starting node {device_id}")
                global global_ui_update_queue
                if global_ui_update_queue:
                    log_data = {"level": "INFO", "message": f"API: Starting node {device_id}"} # Changed level
                    # Use await put()
                    await global_ui_update_queue.put(("log_event", log_data))

                # MUST await the async start method
                await node_to_start.start()
                
                return web.Response(text=f"Node {device_id} start initiated.")

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
        if node_to_modify: # Simplified check
            print(f"API: Setting node {device_id} active state to {target_active_state}")
            global global_ui_update_queue
            state_str = "active" if target_active_state == 2 else "inactive"
            if global_ui_update_queue:
                 log_data = {"level": "WARN", "message": f"API: Setting node {device_id} to {state_str}."}
                 # Use await put()
                 await global_ui_update_queue.put(("log_event", log_data))

            # Call the appropriate method on the node instead of direct attribute access
            if target_active_state == 0: # Deactivate
                 if hasattr(node_to_modify, 'deactivate') and callable(node_to_modify.deactivate):
                     node_to_modify.deactivate() # Assuming deactivate is sync
                 else: print(f"WARN: Node {device_id} has no deactivate method.")
            elif target_active_state == 1: # Reactivate (if needed)
                 if hasattr(node_to_modify, 'reactivate') and callable(node_to_modify.reactivate):
                     node_to_modify.reactivate() # Assuming reactivate is sync
                 else: print(f"WARN: Node {device_id} has no reactivate method.")
            elif target_active_state == 2: # Stay Active (or ensure active)
                 if hasattr(node_to_modify, 'stay_active') and callable(node_to_modify.stay_active):
                     node_to_modify.stay_active() # Assuming stay_active is sync
                 else: print(f"WARN: Node {device_id} has no stay_active method.")
            else:
                 print(f"WARN: Unknown target active state {target_active_state} for node {device_id}")

            #log data
            if global_ui_update_queue:
                 log_data = {"level": "WARN", "message": f"API: Node {device_id} stopping."}
                 await global_ui_update_queue.put(("log_event", log_data))

            node_to_modify._active_value = target_active_state
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

async def process_ui_updates(ui_device: UIDevice, update_queue: asyncio.Queue):
    """Task to read updates from the queue and broadcast them via WebSocket."""
    print("UI Update Processor Task started.")
    while True:
        try:
            update_type, data = await update_queue.get()
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
                
            elif update_type == "message_log" and isinstance(data, dict):
                 print(f"Main Process: Processing message_log from UIDevice: {data}")
                 # The data should already be in the correct format (MessageLogData)
                 # Broadcast directly as 'message_log' type
                 print(f"DEBUG: Main Process broadcasting UIDevice log as message_log: {data}") # <-- ADD DEBUG
                 await ui_device.broadcast_update("message_log", data)
            # Mark the task as done for the asyncio.Queue
            update_queue.task_done()
        except asyncio.CancelledError:
             print("UI Update Processor Task cancelled.")
             break # Exit loop on cancellation
        except Exception as e:
            print(f"Error processing UI update from queue: {e}")
            import traceback
            traceback.print_exc()
            # Avoid busy-looping on persistent errors
            await asyncio.sleep(1)

async def main():
    """
    Main driver for protocol simulation.
    :return:
    """

    args = parse_args()

    # --- Initialize Checkpoint Manager ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True) # Ensure output dir exists
    checkpoint_dir = OUTPUT_DIR / args.checkpoint_dir
    checkpoint_mgr = CheckpointManager(checkpoint_dir)




    # startup
    num_devices = 4  #max tested is 1000


    network = Network()
    nodes = []
    init_tasks = []
    for i in range(num_devices):
        shared_active = 2

        new_node = SimulationNode(i+1, active_value=shared_active, checkpoint_mgr=checkpoint_mgr)  # can we move active to lower level like size?
        nodes.append(new_node)
        #init_tasks.append(new_node.node_id, new_node)  # prepare async initialization tasks
        network.add_node(new_node.node_id, new_node)
    #update device list

    #adding UI device
    # --- Create UIDevice Node and Instance Correctly ---
    ui_device_id = num_devices + 1
    print(f"Creating UI device with ID {ui_device_id}")
    ui_update_queue = asyncio.Queue() 
    global global_ui_update_queue
    global_ui_update_queue = ui_update_queue
    # Pass None for transceiver initially, it gets set by network.add_node
    ui_device = UIDevice(ui_device_id, update_queue=ui_update_queue, transceiver=None)
    ui_shared_active = 2
    

    print(f"Creating UI simulation node with ID {ui_device_id}")
    # 2. Create the SimulationNode for the UI device
    ui_node = SimulationNode(
        node_id=ui_device_id,
        target_func=ui_device.device_main, # Pass the instance method
        active_value=ui_shared_active,
        checkpoint_mgr=checkpoint_mgr
        
    )

    # 3. Add the UI node to the network (this initializes its transceiver)
    print(f"Adding UI node {ui_device_id} to network")
    network.add_node(ui_device_id, ui_node)
    if hasattr(ui_node, 'transceiver'):
        print(f"Assigning transceiver from UI node {ui_device_id} to UIDevice instance")
        ui_device.transceiver = ui_node.transceiver
    else:
        print(f"WARN: UI node {ui_device_id} has no transceiver after being added to network.")
    # 4. Assign the UIDevice instance back to the node AFTER adding to network
    #    The transceiver is automatically assigned by network.add_node
    print(f"Assigning UIDevice instance to UI node {ui_device_id}")
    ui_node.thisDevice = ui_device
    # ui_node.transceiver is handled by network.add_node

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
            simulation_nodes_map[n.node_id] = n
            print(f"Mapping dynamic device ID {n.thisDevice.id} to simulaation node: {getattr(n, 'node_id')}")
        else:
            print(f"WARN: Could not map node (missing node_id attribute): {n}")

        

    
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

     # --- Start Node Main Tasks ---
    node_main_tasks = []
    # Start regular nodes
    for i, node in enumerate(nodes):
        print(f"Starting node {i+1}/{len(nodes)}: {node.node_id}")
        # MUST await the async start method
        await node.start()
        # Store the task created by start() for the final gather
        if hasattr(node, '_main_task') and node._main_task:
             node_main_tasks.append(node._main_task)
        else:
             
             print(f"WARN: Node {node.node_id} did not expose a main task after start.")
    #MUST await the async start method for the UI node too
    await ui_node.start()
    if hasattr(ui_node, '_main_task') and ui_node._main_task:
         node_main_tasks.append(ui_node._main_task)
    else:
         print(f"WARN: UI Node {ui_node.node_id} did not expose a main task after start.")
    # indefinitely awaiting websocket tasks
     # --- Wait Indefinitely (or for specific tasks) ---
    # Gather background tasks AND the main node tasks
    # Remove *started_tasks (init tasks) as they should be complete implicitly before node.start
    tasks_to_wait_for = [ws_server_task, ui_update_processor_task] + node_main_tasks
    print(f"Gathering {len(tasks_to_wait_for)} essential tasks...")
    try:
        # Wait for all essential tasks to complete (which might be never for servers/nodes)
        await asyncio.gather(*tasks_to_wait_for)
        print("Main gather completed (unexpected for long-running tasks).")
    except asyncio.CancelledError:
         print("Main gather was cancelled.")
    except Exception as e:
         print(f"Error during main gather: {e}")
         traceback.print_exc()
    finally:
        print("Cleaning up HTTP runner...")
        await http_runner.cleanup()
        # Optional: Add explicit node stopping logic here if needed on exit
        print("Stopping node tasks...")
        for task in node_main_tasks:
             if not task.done():
                 task.cancel()
        # Allow cancellations to process
        await asyncio.sleep(0.1)
        print("Cleanup finished.")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    duration = end_time - start_time
    minutes = int(duration // 60)
    remaining_seconds = duration % 60
    seconds = int(remaining_seconds)
    milliseconds = int((remaining_seconds - seconds) * 1000)
    print(f"Total time taken: {minutes:02d}:{seconds:02d}:{milliseconds:03d}")
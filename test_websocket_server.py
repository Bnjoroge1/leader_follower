import asyncio
import websockets
import json

async def handler(websocket):
    print("Client connected")
    
    # Send initial state
    await websocket.send(json.dumps({
        "type": "initial_state",
        "device_id": "5",
        "leader_id": "1",
        "is_leader": False,
        "is_follower": True,
        "device_list": [
            {"id": "1", "task": 1, "leader": True, "missed": 0},
            {"id": "2", "task": 2, "leader": False, "missed": 0},
            {"id": "3", "task": 3, "leader": False, "missed": 0},
            {"id": "4", "task": 4, "leader": False, "missed": 0}
        ]
    }))
    
    # Also send a device list update
    await websocket.send(json.dumps({
        "type": "device_list",
        "timestamp": 1234567890,
        "data": [
            {"id": "1", "task": 1, "leader": True, "missed": 0},
            {"id": "2", "task": 2, "leader": False, "missed": 0},
            {"id": "3", "task": 3, "leader": False, "missed": 0},
            {"id": "4", "task": 4, "leader": False, "missed": 0}
        ]
    }))
    
    # Handle incoming messages
    async for message in websocket:
        print(f"Received message: {message}")
        
        # Echo the message back
        await websocket.send(message)

async def main():
    print("Starting WebSocket server on port 8765")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())

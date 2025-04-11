import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8765"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Send a test message
            await websocket.send(json.dumps({"type": "test"}))
            print("Sent test message")
            
            # Wait for a response
            response = await websocket.recv()
            print(f"Received response: {response}")
    except Exception as e:
        print(f"Error connecting to WebSocket server: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())

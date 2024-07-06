import React, {useState, useEffect} from 'react';
import { ForceGraph2D } from 'react-force-graph';
import io from 'socket.io-client';


// Define the App component
function App() {


    // Connect to the server
  const socket = new WebSocket('ws://localhost:3000');
  socket.addEventListener('open', () => {
    console.log('Connected to WS server!');
    sendMessage();
  });
  socket.addEventListener('message', (event) => {
    console.log('Message from server:', event.data);
  });

  const sendMessage = () => {
    socket.send('Hello from the client!');
  };

  return (
    <div>
      <h1>WebSockets Example</h1>
      <button onClick={sendMessage}>Send Message</button>
    </div>
  );

}

export default App;
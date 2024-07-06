import React, { useEffect, useRef } from 'react';


// Define the App component
function App() {
  const socket = useRef(null);

  useEffect(() => {
  // Connect to the server
  socket.current = new WebSocket('ws://localhost:3000');
  // log when the connection is opened
  socket.current.addEventListener('open', () => {
    console.log('Connected to WS server!');
    socket.current.send('Hello from the client!')  // placement should wait for connection
  });

  // receive messages from the server
  socket.current.addEventListener('message', (event) => {
    console.log('Message from server:', event.data);
  });

  const buttons = document.querySelectorAll('#control-buttons button');
  const handleClicks = [];

  buttons.forEach((button, index) => {
    const handleClick = (event) => {
      button.style.animation = 'flash 0.5s';
      console.log("Button clicked:", event.target.textContent)
      // ensure the socket is open before sending
      if (socket.current.readyState === WebSocket.OPEN) {
        socket.current.send(event.target.textContent);
      } else {
        console.error("WebSocket is not open. Current state:", socket.current.readyState);
      }
      button.addEventListener('animationend', () => {
        button.style.animation = 'none';
      });
    };

    handleClicks[index] = handleClick;  // storing reference for cleanup
    button.addEventListener('click', handleClick);
  });

  // cleanup function to remove event listeners
  return () => {
    buttons.forEach((button, index) => {
      button.removeEventListener('click', handleClicks[index]);
    });
  };
}, []);

  return (
    <div id="control-div">
      <h1 id="control-title">Control Panel</h1>
      <div id="control-buttons">
        <button>Create Device</button>
        <button>Delete Device</button>
        <button>Toggle Device</button>
        <button>Toggle Simulation</button>
      </div>
    </div>
  );

}

export default App;
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
    socket.current.send('CONNECTED,FRONTEND')  // placement should wait for connection
  });

  // receive messages from the server
  socket.current.addEventListener('message', (event) => {
    console.log('Message from server:', event.data);
    let message = event.data.toString();
    const parts = message.split(',');
    
    if (parts[0] === 'CONNECTED') {
      displayDevice(parts[1]);
    }
  });

  function displayDevice(deviceId) {
    const container = document.getElementById('device-container');
    if (!container) {
      return;
    }

    const newDevice = document.createElement('div');
    newDevice.id = `device-${deviceId}`;
    newDevice.style.position = 'absolute';
    newDevice.style.width = '30px';
    newDevice.style.height = '30px';
    newDevice.style.borderRadius = '50%';
    newDevice.style.backgroundColor = 'skyblue';

    const label = document.createElement('div');
    label.textContent = deviceId;  // should already be a string
    label.style.position = 'absolute';
    label.style.textAlign = 'center';
    label.style.width = '100%';
    label.style.top = '-20px';

    container.appendChild(newDevice);
    newDevice.appendChild(label);

    const devices = container.children;
    const numberOfDevices = devices.length;
    const radius = 280;

    for (let i = 0; i < numberOfDevices; i++) {
      const angle = (i / numberOfDevices) * Math.PI * 2;  // angle in radians
      const x = radius * Math.cos(angle) + container.offsetWidth / 2;
      const y = radius * Math.sin(angle) + container.offsetHeight / 2;

      devices[i].style.left = `${x}px`;
      devices[i].style.top = `${y}px`;
    }
  }

  const buttons = document.querySelectorAll('#control-buttons button');
  const handleClicks = [];

  buttons.forEach((button, index) => {
    const handleClick = (event) => {
      button.style.animation = 'flash 0.5s';
      console.log("Button clicked:", event.target.textContent)
      // ensure the socket is open before sending
      if (socket.current.readyState === WebSocket.OPEN) {
        socket.current.send(`INJECT,${event.target.textContent}`);
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
    <>
    <div id="parent">
      <div id="control-div">
        <h1 id="control-title">Control Panel</h1>
        <div id="control-buttons">
          <button>Create Device</button>
          <button>Delete Device</button>
          <button>Toggle Device</button>
          <button>Toggle Simulation</button>
        </div>
      </div>

      <div id="device-container">
        <div id="active-devices">
        </div>
        
        <div id="reserve-devices">

        </div>
      </div>
    </div>
    </>
  );

}

export default App;
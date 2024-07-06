import React, { useEffect } from 'react';


// Define the App component
function App() {

  useEffect(() => {
    const buttons = document.querySelectorAll('#control-buttons button');
    buttons.forEach((button) => {
      button.addEventListener('click', (event) => {
        button.style.animation = 'flash 0.5s';
        socket.send(event.target.textContent);
        button.addEventListener('animationend', () => {
          button.style.animation = 'none';
        });
      })
  });
}, []);


    // Connect to the server
  const socket = new WebSocket('ws://localhost:3000');
  socket.addEventListener('open', () => {
    console.log('Connected to WS server!');
    socket.send('Hello from the client!')
  });
  socket.addEventListener('message', (event) => {
    console.log('Message from server:', event.data);
  });

  const createDevice = () => {
    socket.send('Create a new device!');
  };

  const deleteDevice = () => {
    socket.send('Delete a device!');
  };

  const pauseDevice = () => {
    socket.send('Pause a device!');
  };

  const toggleSimulation = () => {
    socket.send('Toggle simulation!');
  };

  document.getElementById

  return (
    <div id="control-div">
      <h1 id="control-title">Control Panel</h1>
      <div id="control-buttons">
        <button onClick={createDevice}>Create Device</button>
        <button onClick={deleteDevice}>Delete Device</button>
        <button onClick={pauseDevice}>Toggle Device</button>
        <button onClick={toggleSimulation}>Toggle Simulation</button>
      </div>
    </div>
  );

}

export default App;
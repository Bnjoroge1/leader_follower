import React, {useState, useEffect} from 'react';
import { ForceGraph2D } from 'react-force-graph';
import io from 'socket.io-client';

// Connect to the server
const socket = io('http://localhost:3001');

// Define the App component
function App() {

  // Define the state variables
  const [nodes, setNodes] = useState([]);
  const[links, setLinks] = useState([]);

  // Update the state variables when the server sends data
  useEffect(() => {
    socket.on('data', data => {
      setNodes(data.nodes);
      setLinks(data.links);
    });

    // Clean up the effect to prevent memory leaks
    return () => socket.off('data');
  }, []);

  return (
    <div>
      <ForceGraph2D
        graphData={{ nodes, links }}
        nodeLabel="id"
        nodeAutoColorBy="group"
      />
    </div>
  );
}

export default App;
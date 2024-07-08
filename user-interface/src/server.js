const express = require('express');
const app = express();
const server = require('http').Server(app);
const WebSocket = require('ws');
const wss = new WebSocket.Server({ server: server });
var frontend = null;

// TODO: should we save a ws : node id mapping or have transceivers send their id?
wss.on('connection', function connection(ws) {
    console.log('New client connected!');
    ws.send('Welcome to the server!');

    ws.on('close', function close() {
        console.log('Client disconnected');
    });

    ws.on('message', function incoming(message) {
        console.log('received: %s', message);
        message = message.toString();  // convert to string, is this ok?
        const parts = message.split(',');
        const tag = parts[0];
        const id = parts[1];

        if (['CONNECTED', 'SENT', 'RCVD', 'REACTIVATED', 'DEACTIVATED'].includes(tag)) {  // consider switching to hashset
            if (id === 'FRONTEND') {  // only applies to CONNECTED
                frontend = ws;  // store frontend reference
            } else {
                if (frontend) {
                    frontend.send(message);  // relay to frontend
                }
            }
        } else if (tag === 'INJECT') {  // right now is relaying to all clients (devices)
            wss.clients.forEach(function each(client) {
                // filter out the sender
                if (client !== ws && client.readyState === WebSocket.OPEN) {
                    client.send(id);
                }
            });
        }
    });
});

app.get('/', (req, res) => {
    res.send('Hello World!');
});

server.listen(3000, () => {
    console.log('Server listening on port 3000');
});
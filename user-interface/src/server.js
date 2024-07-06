const express = require('express');
const app = express();
const server = require('http').Server(app);
const WebSocket = require('ws');
const wss = new WebSocket.Server({ server: server });

wss.on('connection', function connection(ws) {
    console.log('New client connected!');
    ws.send('Welcome to the server!');

    ws.on('message', function incoming(message) {
        console.log('received: %s', message);

        // relay message to all clients (protocol generalized to one channel)
        // the protocol is responsible for virtual directed messages and filtering
        // TODO: message encryption
        wss.clients.forEach(function each(client) {
            // filter out the sender
            if (client !== ws && client.readyState === WebSocket.OPEN) {
                client.send('Relayed: ' + message);
            }
        });
    });
});

app.get('/', (req, res) => {
    res.send('Hello World!');
});

server.listen(3000, () => {
    console.log('Server listening on port 3000');
});
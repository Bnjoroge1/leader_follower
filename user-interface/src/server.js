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
        
        // relay message to all clients (protocol generalized to one channel)
        // the protocol is responsible for virtual directed messages and filtering
        // TODO: message encryption

        // TODO: format inject into INJECT:ACTION,ID
        // right now is just INJECT,ACTION and hits all devices
        if (parts[0] === 'INJECT') {
            wss.clients.forEach(function each(client) {
                // filter out the sender
                if (client !== ws && client.readyState === WebSocket.OPEN) {
                    // client.send('Relayed: ' + message);
                    client.send(parts[1]);  // TODO: may want to send ACTION,ID instead
                }
            });
        // messages take the form of ACTION,ID
        // TODO: can probably clean this logic up
        } else if (parts[0] === 'CONNECTED' || parts[0] === 'DISCONNECTED') {  
            // transceiver websockets will connect and disconnect (to stay async?), ignore those
            // only CONNECTED and DISCONNECTED messages are relevant
            if (parts[1] === 'FRONTEND') {
                frontend = ws;  // store frontend reference
            } else {
                if (frontend) {
                    frontend.send(message);  // relay to frontend
                }
            }
        } else if (parts[0] === 'SENT' || parts[0] === 'RCVD') {
            if (frontend) {
                frontend.send(message);  // relay to frontend
            }
        }
    });
});

app.get('/', (req, res) => {
    res.send('Hello World!');
});

server.listen(3000, () => {
    console.log('Server listening on port 3000');
});
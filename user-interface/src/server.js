const express = require('express');
const app = express();
const server = require('http').Server(app);
const WebSocket = require('ws');
const wss = new WebSocket.Server({ server: server });
var frontend = null;
var backend = null;

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

        if (tag === "NEW") {
            frontend.send(message);  // relay to frontend
        } else if (tag === "DEAD") {
            frontend.send(message);  // relay to frontend
        } else if (tag === "FOLLOWER") {
            frontend.send(message);  // relay to frontend
        } else if (tag === "LEADER") {
            frontend.send(message);  // relay to frontend
        } else if (tag === "TOGGLE") {
            backend.send(message);
        } else if (tag === "CONNECTED") {
            if (id === "FRONTEND") {
                frontend = ws;
            } else if (id === "BACKEND") {
                backend = ws;
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


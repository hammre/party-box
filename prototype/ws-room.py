#!/usr/bin/env python3
# requires python websocket-client

import websocket
import pprint
import json
s = websocket.WebSocket()
s.connect("ws://localhost:9000")
s.send(json.dumps({
    "command": "create-room",
    "user-agent": "Test room creator",
    "participant-name": "TestRoom",
    "capabilities": []}).encode('utf-8'))
while True:
    try:
        pprint.pprint(json.loads(s.recv()))
    except KeyboardInterrupt:
        break
s.close()

#!/usr/bin/env python3
# Requires python websocket-client
import websocket
import pprint
import sys
import json
s = websocket.WebSocket()
s.connect("ws://localhost:9000")
s.send(json.dumps({
    "command": "join-room",
    "user-agent": "Test room joiner",
    "participant-name": sys.argv[1],
    "capabilities": [],
    "room-code": sys.argv[2]}).encode('utf-8'))
while True:
    try:
        pprint.pprint(json.loads(s.recv()))
    except KeyboardInterrupt:
        break
s.close()

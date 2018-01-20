#!/usr/bin/env python3
# Requires python websocket-client
import websocket
import pprint
import sys
import json
from messages import JoinRoomMessage
s = websocket.WebSocket()
s.connect("ws://localhost:9000")
m = JoinRoomMessage(sys.argv[2], sys.argv[1], user_agent="Test Room Joiner",
        capabilities=[])
s.send(m.encode())
while True:
    try:
        pprint.pprint(json.loads(s.recv()))
    except KeyboardInterrupt:
        break
s.close()

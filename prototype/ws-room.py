#!/usr/bin/env python3
# requires python websocket-client

import websocket
import pprint
import json
from messages import CreateRoomMessage
s = websocket.WebSocket()
s.connect("ws://localhost:9000")
m = CreateRoomMessage([], name="TestRoom", user_agent="Test Room Creator")
s.send(m.encode())
while True:
    try:
        pprint.pprint(json.loads(s.recv()))
    except KeyboardInterrupt:
        break
s.close()

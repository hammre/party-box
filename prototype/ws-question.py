#!/usr/bin/env python3
# requires python websocket-client

import websocket
from pprint import pprint
import json
from messages import CreateRoomMessage, SimpleMultiChoiceQuestion
s = websocket.WebSocket()
s.connect("ws://localhost:9000")
m = CreateRoomMessage(["multi-choice"], name="Quizmaster", user_agent="Multi-Choice prototype Game")
s.send(m.encode())
while True:
    try:
        msg = json.loads(s.recv())
        if msg.get('command', None) == 'participant-status':
            if msg.get('presence', None) == 'connected':
                m = SimpleMultiChoiceQuestion(room, msg.get('participant-name', None), "What is your choice of meal?",
                        ["Pizza", "Burgers", "Fish Fry", "Full Diner Breakfast"])
                s.send(m.encode())
        elif msg.get('command', None) == 'participant-message':
            pprint(msg)
        elif msg.get('command', None) == 'create-room-response':
            if msg['status'] != 0:
                print("Error creating room: {}".format(msg))
                break
            room = msg['room-code']
        else:
            print("Unknown message")
            pprint(msg)
    except KeyboardInterrupt:
        break
s.close()
#!/usr/bin/env python3
# Requires python websocket-client
import websocket
from pprint import pprint
import sys
import json
from messages import JoinRoomMessage, SimpleMultiChoiceAnswer
s = websocket.WebSocket()
s.connect("ws://localhost:9000")
m = JoinRoomMessage(sys.argv[2], sys.argv[1], user_agent="Test Room Joiner",
        capabilities=['multi-choice'])
s.send(m.encode())
while True:
    try:
        m = json.loads(s.recv())
        if m.get('command', None) == 'participant-message':
            reply_to = m['from']
            qid = m.get('question-identifier', None)
            if qid is None:
                print("Unknown message")
                pprint(m)
                continue

            prompt = m.get('Prompt', '')
            choices = m['choices']
            selection = None
            while selection is None:
                print(prompt)
                for i, choice in enumerate(choices):
                    print("[{}] {}".format(i, choice['label']))
                idx = input("> ")
                try:
                    n_idx = int(idx)
                    selection = choices[n_idx]
                except (ValueError, IndexError):
                    continue

            a = SimpleMultiChoiceAnswer(sys.argv[2], reply_to, qid, selection)
            s.send(a.encode())
        else:
            print("Unknown message")
            pprint(m)

    except KeyboardInterrupt:
        break
s.close()
